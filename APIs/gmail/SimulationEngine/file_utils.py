"""
Simple File Utilities for Google Agents API

Basic file handling utilities for reading/writing files and encoding/decoding.
Supports text files (.py, .js, .html, .xml, .csv, etc.) and binary files (pdf, jpg, png, xlsx, etc.)
"""

import os
import base64
import mimetypes
import hashlib
import uuid
from typing import Dict, Any, Union, List, Optional
from datetime import datetime

# Text file extensions
TEXT_EXTENSIONS = {
    # Core Programming Languages
    '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.cxx', '.cc', '.cs', '.php', '.rb', '.go', 
    '.rs', '.swift', '.kt', '.scala', '.clj', '.cljs', '.hs', '.ml', '.mli', '.fs', '.fsx', '.elm', 
    '.dart', '.lua', '.pl', '.pm', '.r', '.jl', '.nim', '.zig', '.odin',
    
    # Web & Frontend
    '.html', '.htm', '.xml', '.xhtml', '.svg', '.css', '.scss', '.sass', '.less', '.jsx', '.tsx',
    '.vue', '.svelte', '.astro', '.ejs', '.hbs', '.handlebars', '.mustache', '.pug', '.jade',
    
    # Configuration & Data
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.config', '.env', '.properties',
    '.csv', '.tsv', '.txt', '.md', '.rst', '.adoc', '.tex', '.latex', '.bib', '.log',
    
    # Database & API
    '.sql', '.graphql', '.gql', '.proto', '.thrift', '.avro', '.parquet', '.feather', '.arrow',
    
    # Shell & Scripts
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.rc', '.profile', '.bashrc', '.zshrc',
    
    # Build & Project Files
    '.gradle', '.sbt', '.cmake', '.make', '.makefile', '.dockerfile', '.containerfile', '.gitignore',
    '.gitattributes', '.editorconfig', '.eslintrc', '.prettierrc', '.babelrc', '.npmrc', '.yarnrc',
    
    # Assembly & System
    '.asm', '.s', '.S', '.f90', '.f95', '.f03', '.f', '.for', '.pas', '.ada', '.adb', '.ads',
    '.cob', '.cobol', '.cbl',
    
    # Documentation & Text
    '.rtx', '.nfo', '.readme', '.changelog', '.license', '.authors', '.contributors', '.todo',
    '.notes', '.draft', '.memo',
    
    # Template & Markup
    '.tpl', '.tmpl', '.template', '.jinja', '.j2', '.erb', '.haml', '.slim', '.twig',
    
    # Mobile & Specialized
    '.m', '.mm', '.plist', '.xcconfig', '.pbxproj', '.storyboard', '.xib',
    
    # Data Science & Research
    '.ipynb', '.rmd', '.rnw', '.sage', '.maxima', '.maple', '.mathematica', '.m', '.nb',
    
    # Game Development
    '.cs', '.shader', '.hlsl', '.glsl', '.cg', '.fx',
    
    # Misc Code
    '.vim', '.vimrc', '.tmux', '.zprofile', '.bashprofile', '.inputrc', '.screenrc'
}

# Binary file extensions
BINARY_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.ico', '.cur',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp', '.rtf',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.lzma', '.lz4', '.zstd',
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.mp4', '.avi', '.mov', '.wmv',
    '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.mpg', '.mpeg', '.mts', '.m2ts',
    '.exe', '.dll', '.so', '.dylib', '.bin', '.app', '.deb', '.rpm', '.msi', '.pkg',
    '.apk', '.ipa', '.jar', '.war', '.ear', '.class', '.pyc', '.pyo', '.pyd',
    '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.fdb', '.odb',
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    '.obj', '.fbx', '.dae', '.3ds', '.max', '.blend', '.ma', '.mb', '.c4d', '.stl',
    '.step', '.stp', '.iges', '.igs', '.dwg', '.dxf',
    '.iso', '.img', '.vmdk', '.vhd', '.vhdx', '.ova', '.ovf', '.qcow2', '.vdi'
}

# Supported MIME types for Gmail attachments
SUPPORTED_MIME_TYPES = {
    # Documents
    'application/pdf', 'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/rtf', 'application/vnd.oasis.opendocument.text',
    'application/vnd.oasis.opendocument.spreadsheet',
    'application/vnd.oasis.opendocument.presentation',
    
    # Images
    'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
    'image/svg+xml', 'image/tiff', 'image/x-icon',
    
    # Text & Code Files
    'text/plain', 'text/html', 'text/css', 'text/javascript', 'text/csv',
    'application/json', 'application/xml', 'text/xml',
    'text/x-python', 'text/x-java-source', 'text/x-c', 'text/x-c++src', 'text/x-csharp',
    'text/x-php', 'text/x-ruby', 'text/x-go', 'text/x-rust', 'text/x-swift',
    'text/x-scala', 'text/x-clojure', 'text/x-haskell', 'text/x-lua', 'text/x-perl',
    'text/x-r', 'text/x-julia', 'text/x-dart', 'text/x-elm', 'text/x-nim',
    'text/x-sh', 'application/x-sh', 'text/x-shellscript',
    'application/x-yaml', 'text/yaml', 'application/toml', 'text/markdown',
    'text/x-sql', 'application/sql', 'text/x-dockerfile',
    'application/x-httpd-php', 'text/x-component', 'text/x-vue',
    
    # Archives
    'application/zip', 'application/x-rar-compressed', 'application/x-tar',
    'application/gzip', 'application/x-7z-compressed',
    
    # Audio/Video
    'audio/mpeg', 'audio/wav', 'audio/flac', 'audio/aac', 'audio/ogg',
    'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo',
    'video/webm', 'video/x-matroska',
    
    # Other
    'application/octet-stream'
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

def validate_file_type(file_path: str) -> bool:
    """
    Validate if file type is supported for Gmail attachments.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file type is supported, False otherwise
    """
    ext = os.path.splitext(file_path)[1].lower()
    mime_type = get_mime_type(file_path)
    
    # Check if extension is known (either text or binary)
    if ext not in TEXT_EXTENSIONS and ext not in BINARY_EXTENSIONS:
        return False
    
    # Also check MIME type
    return mime_type in SUPPORTED_MIME_TYPES

def generate_attachment_id(prefix: str = "att") -> str:
    """
    Generate a unique attachment ID.
    
    Args:
        prefix: Prefix for the attachment ID
        
    Returns:
        Unique attachment ID string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_id}"

def calculate_checksum(file_data: bytes) -> str:
    """
    Calculate SHA256 checksum for byte data.
    
    Args:
        file_data: Binary data
        
    Returns:
        SHA256 checksum in format "sha256:hash"
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_data)
    return f"sha256:{sha256_hash.hexdigest()}"

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

def encode_file_to_base64(file_path: str) -> Dict[str, Any]:
    """
    Encode a file to base64 with metadata.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file metadata and base64 content
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not validate_file_type(file_path):
        raise ValueError(f"Unsupported file type: {file_path}")
    
    file_data = read_file(file_path)
    
    # If it's already base64 encoded, return as is
    if file_data['encoding'] == 'base64':
        base64_content = file_data['content']
    else:
        # Encode text to base64
        base64_content = encode_to_base64(file_data['content'])
    
    # Read raw bytes for checksum
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    
    return {
        'filename': os.path.basename(file_path),
        'fileSize': file_data['size_bytes'],
        'mimeType': file_data['mime_type'],
        'data': base64_content,
        'checksum': calculate_checksum(file_bytes),
        'uploadDate': datetime.now().isoformat() + "Z",
        'encoding': 'base64'
    }

def decode_base64_to_file(attachment_data: Dict[str, Any], output_path: str) -> bytes:
    """
    Decode base64 attachment data to file and return bytes.
    
    Args:
        attachment_data: Dictionary containing base64 data
        output_path: Path where to save the decoded file
        
    Returns:
        Decoded bytes
    """
    if 'data' not in attachment_data:
        raise ValueError("Attachment data missing 'data' field")
    
    base64_content = attachment_data['data']
    decoded_bytes = decode_from_base64(base64_content)
    
    # Write to file if output path provided
    if output_path:
        base64_to_file(base64_content, output_path)
    
    return decoded_bytes


class FileProcessor:
    """
    Comprehensive file processing utility class for Gmail attachments.
    Handles encoding, decoding, validation, and metadata generation.
    """
    
    def __init__(self, max_size_mb: int = 25):
        """
        Initialize FileProcessor.
        
        Args:
            max_size_mb: Maximum file size in MB
        """
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
    
    def encode_file_to_base64(self, file_path: str) -> Dict[str, Any]:
        """
        Encode a file to base64 with full metadata.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with complete attachment metadata
        """
        return encode_file_to_base64(file_path)
    
    def decode_base64_to_file(self, attachment_data: Dict[str, Any], output_path: str = None) -> bytes:
        """
        Decode base64 attachment data to file.
        
        Args:
            attachment_data: Dictionary containing attachment metadata and base64 data
            output_path: Optional path where to save the decoded file
            
        Returns:
            Decoded bytes
        """
        return decode_base64_to_file(attachment_data, output_path)
    
    def validate_file_type(self, file_path: str) -> bool:
        """
        Validate if file type is supported.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if supported, False otherwise
        """
        return validate_file_type(file_path)
    
    def generate_attachment_id(self, prefix: str = "att") -> str:
        """
        Generate unique attachment ID.
        
        Args:
            prefix: Prefix for the ID
            
        Returns:
            Unique attachment ID
        """
        return generate_attachment_id(prefix)
    
    def calculate_checksum(self, file_data: bytes) -> str:
        """
        Calculate SHA256 checksum for file data.
        
        Args:
            file_data: Binary file data
            
        Returns:
            SHA256 checksum
        """
        return calculate_checksum(file_data)
    
    def validate_file_size(self, file_path: str) -> bool:
        """
        Check if file size is within limits.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if within limits, False otherwise
        """
        if not os.path.exists(file_path):
            return False
        
        file_size = os.path.getsize(file_path)
        return file_size <= self.max_size_bytes
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        mime_type = get_mime_type(file_path)
        
        return {
            'filename': os.path.basename(file_path),
            'fileSize': file_size,
            'mimeType': mime_type,
            'isTextFile': is_text_file(file_path),
            'isBinaryFile': is_binary_file(file_path),
            'isSupported': validate_file_type(file_path),
            'withinSizeLimit': file_size <= self.max_size_bytes,
            'extension': os.path.splitext(file_path)[1].lower()
        }
    
    def get_supported_mime_types(self) -> List[str]:
        """
        Get list of supported MIME types.
        
        Returns:
            List of supported MIME types
        """
        return list(SUPPORTED_MIME_TYPES) 