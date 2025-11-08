import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from APIs.figma.SimulationEngine import file_utils

def test_is_text_file():
    assert file_utils.is_text_file("test.txt")
    assert not file_utils.is_text_file("test.png")

def test_is_binary_file():
    assert file_utils.is_binary_file("test.png")
    assert not file_utils.is_binary_file("test.txt")

def test_get_mime_type():
    assert file_utils.get_mime_type("test.txt") == "text/plain"
    assert file_utils.get_mime_type("test.png") == "image/png"

def test_read_write_file(tmp_path):
    # Text file
    text_file = tmp_path / "test.txt"
    file_utils.write_file(str(text_file), "hello world")
    data = file_utils.read_file(str(text_file))
    assert data["content"] == "hello world"
    assert data["encoding"] == "text"

    # Binary file
    binary_file = tmp_path / "test.bin"
    file_utils.write_file(str(binary_file), b"hello world", encoding="base64")
    data = file_utils.read_file(str(binary_file))
    assert data["content"] == file_utils.encode_to_base64(b"hello world")
    assert data["encoding"] == "base64"

    # File not found
    with pytest.raises(FileNotFoundError):
        file_utils.read_file("nonexistent.txt")

    # File too large
    large_file = tmp_path / "large.txt"
    with open(large_file, "w") as f:
        f.write("a" * (60 * 1024 * 1024))
    with pytest.raises(ValueError):
        file_utils.read_file(str(large_file))

def test_encoding_decoding():
    original_text = "hello world"
    base64_text = file_utils.text_to_base64(original_text)
    assert file_utils.base64_to_text(base64_text) == original_text

    original_bytes = b"hello world"
    base64_bytes = file_utils.encode_to_base64(original_bytes)
    assert file_utils.decode_from_base64(base64_bytes) == original_bytes

def test_file_to_base64_and_back(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello world")
    base64_content = file_utils.file_to_base64(str(file_path))

    new_file_path = tmp_path / "test2.txt"
    file_utils.base64_to_file(base64_content, str(new_file_path))
    assert new_file_path.read_text() == "hello world"
