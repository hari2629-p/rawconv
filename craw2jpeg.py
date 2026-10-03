#!/usr/bin/env python3
"""
C-RAW to JPEG Batch Converter CLI
Fast, high-quality Canon C-RAW / CR3 / CR2 and Camera RAW converter.
"""

import sys
import os
import argparse
import time
import glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn
)
from rich import box

from converter import (
    ConversionOptions,
    ConversionResult,
    convert_file,
    is_raw_file,
    RAW_EXTENSIONS
)

console = Console()


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human readable string (KB, MB, GB)."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def collect_raw_files(
    input_targets: List[str],
    recursive: bool = False
) -> List[Path]:
    """
    Collect all matching RAW files from a list of paths, glob patterns, or folders.
    """
    found_files: List[Path] = []
    seen = set()

    for target in input_targets:
        # Check if target contains glob wildcards
        if any(char in target for char in ["*", "?", "["]):
            matched = glob.glob(target, recursive=recursive)
            for m in matched:
                p = Path(m).resolve()
                if p.is_file() and is_raw_file(p) and p not in seen:
                    found_files.append(p)
                    seen.add(p)
            continue

        p = Path(target).resolve()
        if p.is_file():
            if p not in seen:
                found_files.append(p)
                seen.add(p)
        elif p.is_dir():
            pattern = "**/*" if recursive else "*"
            for item in p.glob(pattern):
                if item.is_file() and is_raw_file(item) and item not in seen:
                    found_files.append(item)
                    seen.add(item)
        else:
            console.print(f"[yellow]Warning: Target not found or invalid: {target}[/yellow]")

    return sorted(found_files)


def build_output_path(
    input_file: Path,
    input_base_dir: Path,
    output_dir: Path,
    preserve_subdirs: bool = True
) -> Path:
    """Determine destination JPEG path given input and output roots."""
    if preserve_subdirs and input_base_dir.is_dir():
        try:
            rel_path = input_file.relative_to(input_base_dir)
            out_path = (output_dir / rel_path).with_suffix(".jpg")
        except ValueError:
            out_path = (output_dir / input_file.name).with_suffix(".jpg")
    else:
        out_path = (output_dir / input_file.name).with_suffix(".jpg")
    return out_path


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Canon C-RAW (.craw / .cr3 / .cr2) and camera RAW files to JPEG.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single C-RAW file:
  python craw2jpeg.py photo.cr3

  # Convert all RAW files in a folder to an output directory:
  python craw2jpeg.py ./raw_photos/ -o ./jpeg_photos/

  # Recursively convert with custom quality and 8 threads:
  python craw2jpeg.py ./photos/ -o ./output/ -r -q 90 -t 8

  # Fast conversion using embedded high-res preview:
  python craw2jpeg.py ./photos/ -o ./output/ --mode extract

  # Resize images to max 3840px (4K):
  python craw2jpeg.py ./photos/ -o ./output/ --max-size 3840
        """
    )

    parser.add_argument(
        "inputs",
        nargs="*",
        default=[],
        help="Input RAW file(s), folder(s), or glob pattern(s) (e.g. photos/ or *.cr3)"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Destination directory (for batches) or output file path (for single file)"
    )
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=95,
        help="JPEG quality factor (1-100, default: 95)"
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["develop", "extract", "auto"],
        default="develop",
        help="Conversion mode: 'develop' (RAW sensor demosaic, highest quality), "
             "'extract' (instant embedded JPEG extraction), 'auto' (develop with fallback) [default: develop]"
    )
    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=min(32, (os.cpu_count() or 1) + 4),
        help="Number of parallel worker threads (default: CPU cores + 4)"
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively scan subdirectories for RAW files"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files if they already exist"
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=None,
        help="Maximum width or height in pixels (maintains aspect ratio)"
    )
    parser.add_argument(
        "--half-size",
        action="store_true",
        help="Fast half-resolution demosaic (useful for fast drafts)"
    )
    parser.add_argument(
        "--auto-wb",
        action="store_true",
        help="Use automatic white balance instead of camera white balance"
    )
    parser.add_argument(
        "--brightness",
        type=float,
        default=1.0,
        help="Brightness multiplier for RAW demosaic (default: 1.0)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Display detailed error diagnostics"
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    # Display Header Banner
    console.print(
        Panel(
            "[bold cyan]Canon C-RAW & Camera RAW to JPEG Converter[/bold cyan]\n"
            f"[dim]Supported formats: {', '.join(sorted(list(RAW_EXTENSIONS)[:8]))} ...[/dim]",
            border_style="cyan",
            box=box.ROUNDED
        )
    )

    # If no inputs provided on command line, prompt interactively
    if not args.inputs:
        console.print("[bold yellow]No folder or file specified on command line.[/bold yellow]")
        folder_input = console.input("[bold green]Enter the folder path containing your C-RAW files: [/bold green]").strip(' "\'')
        if not folder_input:
            console.print("[red]No path entered. Exiting.[/red]")
            sys.exit(1)
        args.inputs = [folder_input]
        
        # Ask if subfolders should be included
        rec_choice = console.input("[cyan]Include subfolders recursively? (y/N): [/cyan]").strip().lower()
        if rec_choice in ['y', 'yes']:
            args.recursive = True

    # 1. Collect files
    with console.status("[bold green]Scanning input paths for RAW files...[/bold green]"):
        files = collect_raw_files(args.inputs, recursive=args.recursive)

    if not files:
        console.print("[bold red]No matching RAW files found.[/bold red]")
        sys.exit(1)

    console.print(f"[bold green]Found {len(files)} RAW file(s) to process.[/bold green]")

    # 2. Configure options
    options = ConversionOptions(
        quality=args.quality,
        mode=args.mode,
        use_camera_wb=not args.auto_wb,
        use_auto_wb=args.auto_wb,
        bright=args.brightness,
        half_size=args.half_size,
        max_dimension=args.max_size
    )

    # 3. Determine base input directory for relative structure if output directory is used
    first_input = Path(args.inputs[0]).resolve()
    base_input_dir = first_input if first_input.is_dir() else first_input.parent

    # Check if single file output was specified as a file (e.g. -o output.jpg)
    single_file_target = None
    if len(files) == 1 and args.output and not Path(args.output).is_dir() and Path(args.output).suffix.lower() in [".jpg", ".jpeg"]:
        single_file_target = Path(args.output).resolve()
        output_dir = single_file_target.parent
    elif args.output:
        output_dir = Path(args.output).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = None

    # Prepare jobs
    conversion_tasks: List[Tuple[Path, Path]] = []
    skipped_count = 0

    for f in files:
        if single_file_target:
            out_p = single_file_target
        elif output_dir:
            out_p = build_output_path(f, base_input_dir, output_dir, preserve_subdirs=args.recursive)
        else:
            out_p = f.with_suffix(".jpg")

        if out_p.exists() and not args.overwrite:
            skipped_count += 1
            continue

        conversion_tasks.append((f, out_p))

    if skipped_count > 0:
        console.print(f"[yellow]Skipping {skipped_count} file(s) that already exist (use --overwrite to force).[/yellow]")

    if not conversion_tasks:
        console.print("[bold green]All files are already converted. Nothing to do.[/bold green]")
        return

    console.print(f"[cyan]Starting conversion with {min(args.threads, len(conversion_tasks))} threads (Mode: [bold]{args.mode}[/bold], Quality: [bold]{args.quality}[/bold])...[/cyan]\n")

    results: List[ConversionResult] = []
    start_total_time = time.perf_counter()

    # 4. Multi-threaded conversion with rich progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task("[green]Converting...", total=len(conversion_tasks))

        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            future_to_file = {
                executor.submit(convert_file, in_p, out_p, options): in_p
                for in_p, out_p in conversion_tasks
            }

            for future in as_completed(future_to_file):
                in_p = future_to_file[future]
                try:
                    res = future.result()
                    results.append(res)
                    if not res.success:
                        console.print(f"[red]Failed:[/red] {in_p.name} - {res.error_message}")
                except Exception as exc:
                    results.append(ConversionResult(
                        input_path=in_p,
                        success=False,
                        error_message=str(exc)
                    ))
                    console.print(f"[red]Exception on {in_p.name}:[/red] {exc}")
                finally:
                    progress.advance(task_id)

    total_duration = time.perf_counter() - start_total_time
    success_results = [r for r in results if r.success]
    failed_results = [r for r in results if not r.success]

    total_input_bytes = sum(r.input_size_bytes for r in success_results)
    total_output_bytes = sum(r.output_size_bytes for r in success_results)

    # 5. Display Summary Table
    table = Table(title="Conversion Summary", box=box.ROUNDED)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold white")

    table.add_row("Total Files Processed", str(len(files)))
    table.add_row("Successfully Converted", f"[green]{len(success_results)}[/green]")
    if skipped_count:
        table.add_row("Skipped (Existing)", f"[yellow]{skipped_count}[/yellow]")
    if failed_results:
        table.add_row("Failed", f"[red]{len(failed_results)}[/red]")
    table.add_row("Total RAW Size", format_bytes(total_input_bytes))
    table.add_row("Total JPEG Size", format_bytes(total_output_bytes))
    if total_input_bytes > 0:
        ratio = (1 - (total_output_bytes / total_input_bytes)) * 100
        table.add_row("Space Saved", f"[green]{ratio:.1f}%[/green]")
    table.add_row("Elapsed Time", f"{total_duration:.2f}s")
    if total_duration > 0 and len(success_results) > 0:
        speed = len(success_results) / total_duration
        table.add_row("Conversion Speed", f"{speed:.2f} photos/sec")

    console.print("\n")
    console.print(table)

    if failed_results and args.verbose:
        console.print("\n[bold red]Error Details:[/bold red]")
        for f_res in failed_results:
            console.print(f"- [yellow]{f_res.input_path.name}[/yellow]: {f_res.error_message}")


if __name__ == "__main__":
    main()
