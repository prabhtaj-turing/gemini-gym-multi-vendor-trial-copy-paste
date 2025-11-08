"""
Simple File Utilities for Google Agents API

Basic file handling utilities for reading/writing files and encoding/decoding.
Supports text files (.py, .js, .html, .xml, .csv, etc.) and binary files (pdf, jpg, png, xlsx, etc.)
"""

import os
import base64
import mimetypes
from typing import Dict, Any, Union

# Text file extensions
TEXT_EXTENSIONS = {
    '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt',
    '.html', '.htm', '.xml', '.xhtml', '.svg', '.css', '.scss', '.sass', '.less', '.jsx', '.tsx',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.config', '.env', '.properties',
    '.csv', '.tsv', '.txt', '.md', '.rst', '.adoc', '.tex', '.latex', '.bib', '.log',
    '.sql', '.graphql', '.gql', '.proto', '.thrift', '.avro', '.parquet', '.feather', '.arrow',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.rc', '.profile', '.bashrc', '.zshrc'
}

# Binary file extensions
BINARY_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg', '.ico', '.cur',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp', '.rtf',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.lzma', '.lz4', '.zstd',
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.mp4', '.avi', '.mov', '.wmv',
    '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.mpg', '.mpeg', '.ts', '.mts', '.m2ts',
    '.exe', '.dll', '.so', '.dylib', '.bin', '.app', '.deb', '.rpm', '.msi', '.pkg',
    '.dmg', '.iso', '.img', '.vdi', '.vmdk', '.qcow2', '.raw', '.vhd', '.vhdx'
}

def get_file_extension(file_path: str) -> str:
    """Get the file extension from a file path.
    
    Args:
        file_path (str): The file path to get the extension from.
    
    Returns:
        str: The file extension (including the dot) or empty string if no extension.
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower()

def is_text_file(file_path: str) -> bool:
    """Check if a file is a text file based on its extension.
    
    Args:
        file_path (str): The file path to check.
    
    Returns:
        bool: True if the file is a text file, False otherwise.
    """
    ext = get_file_extension(file_path)
    return ext in TEXT_EXTENSIONS

def is_binary_file(file_path: str) -> bool:
    """Check if a file is a binary file based on its extension.
    
    Args:
        file_path (str): The file path to check.
    
    Returns:
        bool: True if the file is a binary file, False otherwise.
    """
    ext = get_file_extension(file_path)
    return ext in BINARY_EXTENSIONS

def read_file(file_path: str) -> Union[str, bytes]:
    """Read a file and return its contents.
    
    Args:
        file_path (str): The path to the file to read.
    
    Returns:
        Union[str, bytes]: The file contents as string for text files or bytes for binary files.
    
    Raises:
        FileNotFoundError: If the file doesn't exist.
        IOError: If there's an error reading the file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if is_text_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        with open(file_path, 'rb') as f:
            return f.read()

def write_file(file_path: str, content: Union[str, bytes]) -> None:
    """Write content to a file.
    
    Args:
        file_path (str): The path to the file to write.
        content (Union[str, bytes]): The content to write to the file.
    
    Raises:
        IOError: If there's an error writing the file.
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    if isinstance(content, str):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        with open(file_path, 'wb') as f:
            f.write(content)

def encode_file_to_base64(file_path: str) -> str:
    """Encode a file to base64 string.
    
    Args:
        file_path (str): The path to the file to encode.
    
    Returns:
        str: The base64 encoded string of the file.
    """
    content = read_file(file_path)
    if isinstance(content, str):
        content = content.encode('utf-8')
    return base64.b64encode(content).decode('utf-8')

def decode_base64_to_file(base64_string: str, file_path: str) -> None:
    """Decode a base64 string and write it to a file.
    
    Args:
        base64_string (str): The base64 encoded string.
        file_path (str): The path where to write the decoded file.
    """
    content = base64.b64decode(base64_string)
    write_file(file_path, content)

def get_mime_type(file_path: str) -> str:
    """Get the MIME type of a file.
    
    Args:
        file_path (str): The path to the file.
    
    Returns:
        str: The MIME type of the file.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'
