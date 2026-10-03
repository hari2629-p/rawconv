"""
Unit and integration tests for craw2jpeg converter.
"""

import subprocess
import sys
from pathlib import Path
from converter import is_raw_file, RAW_EXTENSIONS, ConversionOptions, convert_file


def test_raw_extension_recognition():
    """Test recognized raw extensions."""
    assert is_raw_file("sample.craw") is True
    assert is_raw_file("PHOTO.CR3") is True
    assert is_raw_file("IMAGE.cr2") is True
    assert is_raw_file("test.arw") is True
    assert is_raw_file("test.nef") is True
    assert is_raw_file("test.dng") is True
    assert is_raw_file("image.jpg") is False
    assert is_raw_file("file.png") is False
    assert is_raw_file("document.pdf") is False
    print("[OK] Extension recognition tests passed!")


def test_missing_file_handling():
    """Test handling of non-existent files."""
    res = convert_file(Path("non_existent_file.craw"))
    assert res.success is False
    assert "not found" in (res.error_message or "").lower()
    print("[OK] Missing file error handling tests passed!")


def test_cli_help():
    """Test CLI runs with --help without error."""
    result = subprocess.run(
        [sys.executable, "craw2jpeg.py", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=Path(__file__).parent
    )
    assert result.returncode == 0
    assert "Convert Canon C-RAW" in result.stdout
    print("[OK] CLI help argument test passed!")


if __name__ == "__main__":
    print("Running converter test suite...")
    test_raw_extension_recognition()
    test_missing_file_handling()
    test_cli_help()
    print("All tests passed successfully!")
