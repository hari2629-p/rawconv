"""
Core RAW/C-RAW to JPEG conversion engine.
Supports Canon CR3 (C-RAW), CR2, CRW, ARW, NEF, DNG, and other camera RAW formats.
Engineered for maximum image fidelity with 100% quality and 4:4:4 chroma subsampling.
"""

import io
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

import rawpy
from PIL import Image, ImageOps

# Setup logging
logger = logging.getLogger("craw2jpeg")

# Supported RAW extensions
RAW_EXTENSIONS = {
    ".craw", ".cr3", ".cr2", ".crw",  # Canon
    ".arw", ".srf", ".sr2",           # Sony
    ".nef", ".nrw",                   # Nikon
    ".dng",                            # Adobe / Generic
    ".raf",                            # Fujifilm
    ".orf",                            # Olympus
    ".rw2",                            # Panasonic
    ".pef", ".ptx",                   # Pentax
    ".3fr", ".fff",                   # Hasselblad
    ".iiq",                            # Phase One
    ".srw",                            # Samsung
    ".raw"                             # Generic
}


@dataclass
class ConversionOptions:
    """Options to control the RAW to JPEG conversion process with maximum quality."""
    quality: int = 100               # 100 = Maximum uncompressed JPEG quality
    subsampling: int = 0             # 0 = 4:4:4 chroma (NO color resolution loss)
    mode: str = "develop"            # 'develop' (RAW demosaic), 'extract' (embedded preview), 'auto'
    use_camera_wb: bool = True
    use_auto_wb: bool = False
    bright: float = 1.0
    half_size: bool = False
    max_dimension: Optional[int] = None
    preserve_exif: bool = True
    optimize: bool = True
    progressive: bool = False        # False for purest standard baseline encoding


@dataclass
class ConversionResult:
    """Result summary of a single file conversion."""
    input_path: Path
    output_path: Optional[Path] = None
    success: bool = False
    method_used: str = "none"
    error_message: Optional[str] = None
    input_size_bytes: int = 0
    output_size_bytes: int = 0
    resolution: Optional[Tuple[int, int]] = None
    duration_sec: float = 0.0


def is_raw_file(file_path: Path | str) -> bool:
    """Check if the given file has a supported camera RAW extension."""
    ext = Path(file_path).suffix.lower()
    return ext in RAW_EXTENSIONS


def extract_embedded_jpeg(raw_path: Path) -> Optional[Image.Image]:
    """
    Extract the embedded camera-processed JPEG from RAW metadata.
    Preserves exact camera color profile and in-camera processing.
    """
    try:
        with rawpy.imread(str(raw_path)) as raw:
            try:
                thumb = raw.extract_thumb()
                if thumb.format == rawpy.ThumbFormat.JPEG:
                    image_stream = io.BytesIO(thumb.data)
                    img = Image.open(image_stream)
                    # Load the image into memory before closing stream
                    img.load()
                    return img
            except (rawpy.LibRawNoThumbnailError, rawpy.LibRawUnsupportedThumbnailError):
                pass
    except Exception as e:
        logger.debug(f"Embedded preview extraction failed for {raw_path}: {e}")
    return None


def develop_raw_image(raw_path: Path, options: ConversionOptions) -> Image.Image:
    """
    Demosaic and develop raw sensor data using LibRaw at maximum fidelity.
    """
    with rawpy.imread(str(raw_path)) as raw:
        # Determine white balance settings
        use_camera_wb = options.use_camera_wb and not options.use_auto_wb
        use_auto_wb = options.use_auto_wb

        # Convert raw to RGB numpy array with highest quality demosaicing
        rgb_array = raw.postprocess(
            use_camera_wb=use_camera_wb,
            use_auto_wb=use_auto_wb,
            bright=options.bright,
            half_size=options.half_size,
            output_color=rawpy.ColorSpace.sRGB,
            output_bps=8,
            no_auto_bright=False,
            auto_bright_thr=0.01,
            demosaic_algorithm=rawpy.DemosaicAlgorithm.AAHD if hasattr(rawpy.DemosaicAlgorithm, 'AAHD') else rawpy.DemosaicAlgorithm.AHD
        )

        img = Image.fromarray(rgb_array)
        return img


def convert_file(
    input_path: Path | str,
    output_path: Optional[Path | str] = None,
    options: Optional[ConversionOptions] = None
) -> ConversionResult:
    """
    Convert a single RAW / C-RAW file to high-quality JPEG format.

    Args:
        input_path: Path to the input RAW file.
        output_path: Destination path for the output JPEG.
        options: ConversionOptions controlling quality, chroma subsampling, resizing, etc.

    Returns:
        ConversionResult detailing success status, paths, sizes, and any error message.
    """
    import time
    start_time = time.perf_counter()

    input_path = Path(input_path).resolve()
    if options is None:
        options = ConversionOptions()

    if not input_path.exists():
        return ConversionResult(
            input_path=input_path,
            success=False,
            error_message=f"Input file not found: {input_path}"
        )

    if output_path is None:
        output_path = input_path.with_suffix(".jpg")
    else:
        output_path = Path(output_path).resolve()

    # Ensure parent output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    input_size = input_path.stat().st_size
    img: Optional[Image.Image] = None
    method_used = "unknown"

    try:
        if options.mode == "extract":
            img = extract_embedded_jpeg(input_path)
            if img is not None:
                method_used = "embedded_camera_jpeg"
            else:
                raise ValueError("No embedded JPEG preview found in RAW file")

        elif options.mode == "develop":
            img = develop_raw_image(input_path, options)
            method_used = "raw_demosaic_hq"

        elif options.mode == "auto":
            try:
                img = develop_raw_image(input_path, options)
                method_used = "raw_demosaic_hq"
            except Exception as e:
                logger.warning(f"RAW demosaic failed ({e}), falling back to embedded preview extraction.")
                img = extract_embedded_jpeg(input_path)
                if img is not None:
                    method_used = "embedded_camera_jpeg (fallback)"
                else:
                    raise RuntimeError(f"Both RAW demosaic and embedded preview failed: {e}")
        else:
            raise ValueError(f"Unknown conversion mode '{options.mode}'.")

        if img is None:
            raise RuntimeError("Failed to decode image from RAW file")

        # Handle EXIF orientation
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Apply resizing if requested
        if options.max_dimension is not None and options.max_dimension > 0:
            width, height = img.size
            if max(width, height) > options.max_dimension:
                ratio = options.max_dimension / float(max(width, height))
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to RGB mode
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Save to JPEG at MAXIMUM quality with 4:4:4 chroma subsampling (no quality degradation)
        save_kwargs: Dict[str, Any] = {
            "format": "JPEG",
            "quality": max(1, min(100, options.quality)),
            "subsampling": options.subsampling,  # 0 = 4:4:4 full color fidelity
            "optimize": options.optimize,
            "progressive": options.progressive
        }

        img.save(str(output_path), **save_kwargs)
        output_size = output_path.stat().st_size
        resolution = img.size
        duration = time.perf_counter() - start_time

        return ConversionResult(
            input_path=input_path,
            output_path=output_path,
            success=True,
            method_used=method_used,
            input_size_bytes=input_size,
            output_size_bytes=output_size,
            resolution=resolution,
            duration_sec=duration
        )

    except Exception as exc:
        duration = time.perf_counter() - start_time
        return ConversionResult(
            input_path=input_path,
            output_path=output_path,
            success=False,
            method_used=method_used,
            error_message=str(exc),
            input_size_bytes=input_size,
            duration_sec=duration
        )
