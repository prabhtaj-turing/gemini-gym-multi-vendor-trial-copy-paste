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
    '.apk', '.ipa', '.jar', '.war', '.ear', '.class', '.pyc', '.pyo', '.pyd',
    '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.fdb', '.odb',
    '.ttf', '.otf', '.woff', '.woff2', '.eot', '.svg',
    '.obj', '.fbx', '.dae', '.3ds', '.max', '.blend', '.ma', '.mb', '.c4d', '.stl',
    '.step', '.stp', '.iges', '.igs', '.dwg', '.dxf',
    '.iso', '.img', '.vmdk', '.vhd', '.vhdx', '.ova', '.ovf', '.qcow2', '.vdi'
}

def is_text_file(file_path: str) -> bool:
    """Check if file is a text file based on extension."""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in TEXT_EXTENSIONS

def is_binary_file(file_path: str) -> bool:
    """Check if file is a binary file based on extension."""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in BINARY_EXTENSIONS

def get_mime_type(file_path: str) -> str:
    """Get MIME type for file."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'

def read_file(file_path: str, max_size_mb: int = 50) -> Dict[str, Any]:
    """
    Read file and return content with metadata.
    
    Args:
        file_path: Path to the file
        max_size_mb: Maximum file size in MB
        
    Returns:
        Dict with: content, encoding, mime_type, size_bytes
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise ValueError(f"File too large: {file_size} bytes (max: {max_size_bytes})")
    
    mime_type = get_mime_type(file_path)
    
    if is_text_file(file_path):
        # Read as text
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                'content': content,
                'encoding': 'text',
                'mime_type': mime_type,
                'size_bytes': file_size
            }
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    return {
                        'content': content,
                        'encoding': 'text',
                        'mime_type': mime_type,
                        'size_bytes': file_size
                    }
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"Could not decode file: {file_path}")
    else:
        # Read as binary and encode as base64
        with open(file_path, 'rb') as f:
            content_bytes = f.read()
        content = base64.b64encode(content_bytes).decode('utf-8')
        return {
            'content': content,
            'encoding': 'base64',
            'mime_type': mime_type,
            'size_bytes': file_size
        }

def write_file(file_path: str, content: Union[str, bytes], encoding: str = 'text') -> None:
    """
    Write content to file.
    
    Args:
        file_path: Path where to write the file
        content: Content to write
        encoding: 'text' or 'base64'
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    if encoding == 'base64':
        # Decode base64 content
        if isinstance(content, str):
            content_bytes = base64.b64decode(content)
        else:
            content_bytes = content
        # Write as binary
        with open(file_path, 'wb') as f:
            f.write(content_bytes)
    else:
        # Write as text
        if isinstance(content, bytes):
            content_str = content.decode('utf-8')
        else:
            content_str = content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content_str)

def encode_to_base64(content: Union[str, bytes]) -> str:
    """Encode content to base64."""
    if isinstance(content, str):
        content = content.encode('utf-8')
    return base64.b64encode(content).decode('utf-8')

def decode_from_base64(base64_content: str) -> bytes:
    """Decode base64 content to bytes."""
    return base64.b64decode(base64_content)

def text_to_base64(text: str) -> str:
    """Convert text to base64."""
    return encode_to_base64(text)

def base64_to_text(base64_content: str) -> str:
    """Convert base64 to text."""
    return decode_from_base64(base64_content).decode('utf-8')

def file_to_base64(file_path: str) -> str:
    """Read file and return base64 encoded content."""
    with open(file_path, 'rb') as f:
        content_bytes = f.read()
    return base64.b64encode(content_bytes).decode('utf-8')

def base64_to_file(base64_content: str, file_path: str) -> None:
    """Write base64 content to file."""
    content_bytes = base64.b64decode(base64_content)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb') as f:
        f.write(content_bytes) 