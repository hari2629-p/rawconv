# 📸 Canon C-RAW & RAW to JPEG Converter (`craw2jpeg`)

A fast, high-performance batch converter for Canon **C-RAW** (`.craw` / `.cr3`), `.cr2`, `.crw`, and other camera RAW formats. 

Preserves **100% uncompromised image quality** (4:4:4 full chroma color resolution) and automatically organizes converted images into a `converted_jpegs/` folder inside your directory.

---

## ✨ Features

- **Uncompromised Quality (100% Quality & 4:4:4 Chroma)**: Saves JPEGs at maximum quality with zero chroma subsampling (no color bleeding or degradation).
- **Auto-Organized Output**: Automatically creates a `converted_jpegs/` folder inside your selected directory so your original RAW files stay untouched and organized.
- **Canon C-RAW & Multi-Format**:
  - Canon: `.craw`, `.cr3` (C-RAW & uncompressed), `.cr2`, `.crw`
  - Sony: `.arw`, `.srf`, `.sr2`
  - Nikon: `.nef`, `.nrw`
  - Adobe: `.dng`
  - Fujifilm: `.raf`
  - Olympus: `.orf`
  - Panasonic: `.rw2`
- **Dual Conversion Modes**:
  - `develop` *(Default)*: Full RAW sensor demosaic powered by LibRaw with camera white balance.
  - `extract`: Instant extraction of camera-rendered high-resolution embedded JPEGs.
- **Multi-threaded Batching**: Utilizes all your CPU cores for high-speed conversion with live terminal progress bars and speed statistics.
- **Recursive Subdirectory Support**: Recursively processes subdirectories while preserving folder structure.

---

## 🚀 Installation

Ensure Python 3.10+ is installed on your computer.

```bash
pip install -r requirements.txt
```

*(Dependencies: `rawpy`, `Pillow`, `piexif`, `rich`)*

---

## 📖 How to Use

### Method 1: Interactive Mode (Simplest)
Just run the script without any arguments:

```bash
python craw2jpeg.py
```
You will be prompted:
1. Paste your folder path (e.g. `C:\Users\USER\Pictures\MyPhotos`)
2. Choose whether to include subfolders (`y/n`)

The converter will automatically convert all files and save them in:
```
C:\Users\USER\Pictures\MyPhotos\converted_jpegs\
```

---

### Method 2: Command-Line / Batch

#### 1. Convert an Entire Folder
```bash
python craw2jpeg.py "C:\Users\USER\Documents\photos"
```
*(All `.jpg` files will be saved in `C:\Users\USER\Documents\photos\converted_jpegs\`)*

#### 2. Convert Folder Recursively (Including Subfolders)
```bash
python craw2jpeg.py "C:\Users\USER\Documents\photos" -r
```

#### 3. Convert to a Custom Output Folder
```bash
python craw2jpeg.py "C:\path\to\raws" -o "D:\Export\JPEGs"
```

#### 4. Ultra-Fast Camera Embedded JPEG Mode
```bash
python craw2jpeg.py "C:\path\to\raws" --mode extract
```

#### 5. Resize to Max Long Edge (e.g., 4K / 3840px)
```bash
python craw2jpeg.py "C:\path\to\raws" --max-size 3840
```

---

## ⚙️ Command-Line Options Reference

| Option | Flag | Description | Default |
| :--- | :--- | :--- | :--- |
| `inputs` | *(positional)* | Folder path(s), file(s), or glob patterns | Prompts interactively |
| `--output` | `-o` | Custom destination directory | `<folder>\converted_jpegs\` |
| `--quality` | `-q` | JPEG quality (1–100) | `100` *(Max Quality)* |
| `--mode` | `-m` | `develop` (Full demosaic), `extract` (Fast preview), or `auto` | `develop` |
| `--threads` | `-t` | Number of concurrent worker threads | `CPU Cores + 4` |
| `--recursive` | `-r` | Recursively scan subfolders | `False` |
| `--overwrite` | | Overwrite existing JPEGs if already converted | `False` |
| `--max-size` | | Maximum long-edge pixel size (maintains aspect ratio) | `None` (Original) |
| `--half-size`| | Fast half-resolution demosaic for quick drafts | `False` |
| `--auto-wb` | | Use automatic white balance instead of camera metadata | `False` |
| `--brightness` | | Brightness adjustment multiplier | `1.0` |
| `--verbose` | `-v` | Display detailed error diagnostics | `False` |

---

## 🧪 Testing

To run the verification test suite:

```bash
python test_converter.py
```
