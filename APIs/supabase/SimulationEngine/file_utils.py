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
    """
    Check if file is a text file based on extension.
    
    This function determines if a file is a text file by comparing its extension
    against a predefined list of text file extensions.
    
    Args:
        file_path (str): The path to the file to check.
        
    Returns:
        bool: True if the file has a text file extension, False otherwise.
    """
    ext = os.path.splitext(file_path)[1].lower()
    return ext in TEXT_EXTENSIONS

def is_binary_file(file_path: str) -> bool:
    """
    Check if file is a binary file based on extension.
    
    This function determines if a file is a binary file by comparing its extension
    against a predefined list of binary file extensions.
    
    Args:
        file_path (str): The path to the file to check.
        
    Returns:
        bool: True if the file has a binary file extension, False otherwise.
    """
    ext = os.path.splitext(file_path)[1].lower()
    return ext in BINARY_EXTENSIONS

def get_mime_type(file_path: str) -> str:
    """
    Get MIME type for file.
    
    This function determines the MIME type of a file based on its extension using
    the mimetypes library. If the MIME type cannot be determined, it returns
    'application/octet-stream' as a default.
    
    Args:
        file_path (str): The path to the file.
        
    Returns:
        str: The MIME type of the file, or 'application/octet-stream' if it cannot be determined.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'

def read_file(file_path: str, max_size_mb: int = 50) -> Dict[str, Any]:
    """
    Read file and return content with metadata.
    
    This function reads a file and returns its content along with metadata such as
    encoding type, MIME type, and file size. It handles both text and binary files,
    automatically detecting the appropriate format based on the file extension.
    For text files, it attempts to decode using UTF-8 first, then falls back to other
    encodings if necessary. For binary files, the content is base64 encoded.
    
    Args:
        file_path (str): Path to the file to read.
        max_size_mb (int): Maximum allowed file size in megabytes. Defaults to 50.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - content: The file content (text or base64 encoded string)
            - encoding: The encoding type ('text' or 'base64')
            - mime_type: The detected MIME type of the file
            - size_bytes: The file size in bytes
            
    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file exceeds the maximum size or cannot be decoded.
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
    
    This function writes content to a file, handling both text and binary data.
    It automatically creates any necessary parent directories if they don't exist.
    For text encoding, the content is written as UTF-8 text. For base64 encoding,
    the content is first decoded from base64 and then written as binary data.
    
    Args:
        file_path (str): Path where to write the file.
        content (Union[str, bytes]): Content to write, either as a string or bytes.
        encoding (str): The encoding of the content, either 'text' or 'base64'. Defaults to 'text'.
        
    Returns:
        None
        
    Raises:
        ValueError: If an invalid encoding is specified.
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
    """
    Encode content to base64.
    
    This function converts either string or bytes content to a base64 encoded string.
    If the input is a string, it is first encoded to UTF-8 bytes before base64 encoding.
    
    Args:
        content (Union[str, bytes]): The content to encode, either as a string or bytes.
        
    Returns:
        str: The base64 encoded content as a string.
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    return base64.b64encode(content).decode('utf-8')

def decode_from_base64(base64_content: str) -> bytes:
    """
    Decode base64 content to bytes.
    
    This function decodes a base64 encoded string back to its original bytes.
    
    Args:
        base64_content (str): The base64 encoded string to decode.
        
    Returns:
        bytes: The decoded content as bytes.
    """
    return base64.b64decode(base64_content)

def text_to_base64(text: str) -> str:
    """
    Convert text to base64.
    
    This function converts a text string to a base64 encoded string by first
    encoding the text to UTF-8 bytes and then encoding to base64.
    
    Args:
        text (str): The text string to convert to base64.
        
    Returns:
        str: The base64 encoded string.
    """
    return encode_to_base64(text)

def base64_to_text(base64_content: str) -> str:
    """
    Convert base64 to text.
    
    This function decodes a base64 encoded string back to a text string,
    assuming the original content was UTF-8 encoded text.
    
    Args:
        base64_content (str): The base64 encoded string to convert.
        
    Returns:
        str: The decoded text string.
    """
    return decode_from_base64(base64_content).decode('utf-8')

def file_to_base64(file_path: str) -> str:
    """
    Read file and return base64 encoded content.
    
    This function reads a file in binary mode and returns its contents
    encoded as a base64 string.
    
    Args:
        file_path (str): The path to the file to read and encode.
        
    Returns:
        str: The base64 encoded content of the file.
    """
    with open(file_path, 'rb') as f:
        content_bytes = f.read()
    return base64.b64encode(content_bytes).decode('utf-8')

def base64_to_file(base64_content: str, file_path: str) -> None:
    """
    Write base64 content to file.
    
    This function decodes base64 content and writes it to a file in binary mode.
    It creates any necessary parent directories if they don't exist.
    
    Args:
        base64_content (str): The base64 encoded content to write.
        file_path (str): The path where the decoded content should be written.
        
    Returns:
        None
    """
    content_bytes = base64.b64decode(base64_content)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb') as f:
        f.write(content_bytes) 