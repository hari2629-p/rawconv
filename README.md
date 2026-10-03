# Canon C-RAW / RAW to JPEG Converter (craw2jpeg)

A high-performance command-line tool to batch convert Canon **C-RAW** (`.craw` / `.cr3`), `.cr2`, `.crw`, and other camera RAW formats into high-quality **JPEG** images.

---

## ⚡ Features

- **Folder Batch Processing**: Pass any folder path to convert all C-RAW/RAW files inside it.
- **Format Support**: Canon C-RAW (`.craw`, `.cr3`, `.cr2`, `.crw`), Sony (`.arw`), Nikon (`.nef`), Adobe DNG (`.dng`), and Fujifilm (`.raf`).
- **High Quality Demosaicing**: Powered by `rawpy` (LibRaw) for pristine sensor data processing, camera white balance, and sRGB color profile.
- **Fast Embedded Extraction (`--mode extract`)**: Instantly extracts full-resolution camera-processed embedded JPEGs.
- **Multi-threaded Batch Conversion**: Utilizes multi-core processing with live terminal progress bars and speed statistics.
- **Recursive Directory Processing**: Process entire folder structures while preserving subdirectories.
- **Customizable**: Quality factor, max resolution resize, auto white-balance, brightness adjustments.

---

## 🚀 Quick Start

### 1. Installation

Ensure Python 3.10+ is installed, then install requirements:

```bash
pip install -r requirements.txt
```

### 2. Usage Examples

#### Convert All Files in a Folder (In-place)
```bash
# Converts all RAW / C-RAW files in the folder and saves .jpg in the same location
python craw2jpeg.py "C:\path\to\your\raw_folder"
```

#### Convert All Files in a Folder into a Separate Output Folder
```bash
# Converts all files in the folder and saves JPEGs into an output directory
python craw2jpeg.py "C:\path\to\input_folder" -o "C:\path\to\output_folder"
```

#### Convert Folder Recursively (Including Subfolders)
```bash
python craw2jpeg.py "C:\path\to\photos" -o "C:\path\to\output" -r
```

#### Interactive Mode (Prompt for Folder Path)
Simply run without arguments:
```bash
python craw2jpeg.py
```

#### Single File Conversion
```bash
# Convert photo.cr3 to photo.jpg
python craw2jpeg.py photo.cr3
```

#### Fast Embedded Preview Extraction
```bash
# Extract high-resolution camera JPEGs instantly
python craw2jpeg.py "C:\path\to\raw_folder" -o "C:\path\to\output" --mode extract
```

#### Resize and Adjust Quality
```bash
# Set JPEG quality to 90 and resize max dimension (4K / 3840px)
python craw2jpeg.py "C:\path\to\raw_folder" -o "C:\path\to\output" -q 90 --max-size 3840
```

---

## 🛠️ Command-Line Options

| Option | Shorthand | Description | Default |
| :--- | :--- | :--- | :--- |
| `inputs` | | Folder path(s), file(s), or glob patterns | *(Optional, prompts if omitted)* |
| `--output` | `-o` | Destination directory for output JPEGs | Same as input directory |
| `--quality` | `-q` | JPEG compression quality (1–100) | `95` |
| `--mode` | `-m` | Conversion mode: `develop`, `extract`, or `auto` | `develop` |
| `--threads` | `-t` | Number of concurrent worker threads | `CPU + 4` |
| `--recursive` | `-r` | Recursively process nested folders | `False` |
| `--max-size` | | Resize long edge to max pixels (preserves aspect ratio) | `None` |
| `--half-size` | | Fast half-resolution demosaic | `False` |
| `--auto-wb` | | Use auto white balance instead of camera metadata | `False` |
| `--brightness`| | Brightness multiplier | `1.0` |
| `--overwrite` | | Overwrite existing output files | `False` |
| `--verbose` | `-v` | Show detailed error messages | `False` |

---

## 🧪 Testing

To run the verification test suite:

```bash
python test_converter.py
```
