"""
Comprehensive test for file_utils module

Tests file reading/writing and encoding/decoding operations with integrity verification.
"""

import os
import unittest
import tempfile
import hashlib


from common_utils.base_case import BaseTestCaseWithErrorHandler
from azure.SimulationEngine.file_utils import (
    read_file, write_file, is_text_file, is_binary_file, get_mime_type,
    encode_to_base64, decode_from_base64, text_to_base64, base64_to_text,
    file_to_base64, base64_to_file
)


class TestFileUtils(BaseTestCaseWithErrorHandler):

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def test_text_file_integrity(self):
        """Test text file reading/writing with integrity verification."""
        print("=== Testing Text File Integrity ===")
        
        # Create original text file with various content
        original_content = """# Test Python File
        def hello_world():
            print("Hello, World!")
            return "Success"

        # Test with special characters
        test_string = "áéíóú ñ ç ß € £ ¥"
        test_numbers = [1, 2, 3, 4, 5]
        test_dict = {"key": "value", "number": 42}

        if __name__ == "__main__":
            hello_world()
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(original_content)
            original_file = f.name
        
        try:
            # Test 1: Read file using file_utils
            file_info = read_file(original_file)
            print(f"✓ File read successfully")
            print(f"  - Encoding: {file_info['encoding']}")
            print(f"  - MIME type: {file_info['mime_type']}")
            print(f"  - Size: {file_info['size_bytes']} bytes")
            
            # Test 2: Write content back to new file
            new_file = original_file + ".copy"
            write_file(new_file, file_info['content'], encoding=file_info['encoding'])
            
            # Test 3: Verify files are identical
            original_hash = self.calculate_file_hash(original_file)
            new_hash = self.calculate_file_hash(new_file)
            
            print(f"✓ File integrity check:")
            print(f"  - Original hash: {original_hash}")
            print(f"  - New file hash:  {new_hash}")
            print(f"  - Files identical: {original_hash == new_hash}")
            
            # Test 4: Verify content matches
            with open(new_file, 'r', encoding='utf-8') as f:
                new_content = f.read()
            
            content_match = original_content == new_content
            print(f"  - Content identical: {content_match}")
            
            if not content_match:
                print(f"  - Content length: original={len(original_content)}, new={len(new_content)}")
                print(f"  - First 100 chars original: {repr(original_content[:100])}")
                print(f"  - First 100 chars new: {repr(new_content[:100])}")
            
            assert original_hash == new_hash, "File hashes don't match"
            assert content_match, "File contents don't match"
            
            os.unlink(new_file)
            
        finally:
            os.unlink(original_file)

    def test_binary_file_integrity(self):
        """Test binary file reading/writing with integrity verification."""
        print("\n=== Testing Binary File Integrity ===")
        
        # Create original binary file (simulating a PNG image)
        original_binary = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82'
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
            f.write(original_binary)
            original_file = f.name
        
        try:
            # Test 1: Read file using file_utils
            file_info = read_file(original_file)
            print(f"✓ File read successfully")
            print(f"  - Encoding: {file_info['encoding']}")
            print(f"  - MIME type: {file_info['mime_type']}")
            print(f"  - Size: {file_info['size_bytes']} bytes")
            print(f"  - Base64 length: {len(file_info['content'])}")
            
            # Test 2: Write content back to new file
            new_file = original_file + ".copy"
            write_file(new_file, file_info['content'], encoding=file_info['encoding'])
            
            # Test 3: Verify files are identical
            original_hash = self.calculate_file_hash(original_file)
            new_hash = self.calculate_file_hash(new_file)
            
            print(f"✓ File integrity check:")
            print(f"  - Original hash: {original_hash}")
            print(f"  - New file hash:  {new_hash}")
            print(f"  - Files identical: {original_hash == new_hash}")
            
            # Test 4: Verify binary content matches
            with open(new_file, 'rb') as f:
                new_binary = f.read()
            
            binary_match = original_binary == new_binary
            print(f"  - Binary content identical: {binary_match}")
            
            if not binary_match:
                print(f"  - Binary length: original={len(original_binary)}, new={len(new_binary)}")
                print(f"  - First 20 bytes original: {original_binary[:20]}")
                print(f"  - First 20 bytes new: {new_binary[:20]}")
            
            assert original_hash == new_hash, "File hashes don't match"
            assert binary_match, "Binary contents don't match"
            
            os.unlink(new_file)
            
        finally:
            os.unlink(original_file)

    def test_base64_conversion_integrity(self):
        """Test base64 conversion functions with integrity verification."""
        print("\n=== Testing Base64 Conversion Integrity ===")
        
        # Test 1: Text to base64 and back
        original_text = "Hello, World! This is a test string with special chars: áéíóú ñ ç ß € £ ¥"
        print(f"Original text: {repr(original_text)}")
        
        # Convert to base64
        base64_content = text_to_base64(original_text)
        print(f"Base64 encoded: {base64_content}")
        
        # Convert back to text
        decoded_text = base64_to_text(base64_content)
        print(f"Decoded text: {repr(decoded_text)}")
        
        text_match = original_text == decoded_text
        print(f"✓ Text conversion integrity: {text_match}")
        assert text_match, "Text conversion failed"
        
        # Test 2: Binary to base64 and back
        original_binary = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
        print(f"Original binary: {original_binary}")
        
        # Convert to base64
        base64_binary = encode_to_base64(original_binary)
        print(f"Base64 encoded: {base64_binary}")
        
        # Convert back to binary
        decoded_binary = decode_from_base64(base64_binary)
        print(f"Decoded binary: {decoded_binary}")
        
        binary_match = original_binary == decoded_binary
        print(f"✓ Binary conversion integrity: {binary_match}")
        assert binary_match, "Binary conversion failed"

    def test_file_to_base64_integrity(self):
        """Test file to base64 conversion with integrity verification."""
        print("\n=== Testing File to Base64 Integrity ===")
        
        # Create test files
        test_files = [
            ("text.txt", "This is a test text file with content."),
            ("data.json", '{"key": "value", "number": 42, "array": [1, 2, 3]}'),
            ("script.py", "def test_function():\n    return 'Hello, World!'"),
        ]
        
        for filename, content in test_files:
            print(f"\nTesting {filename}:")
            
            # Create original file
            with tempfile.NamedTemporaryFile(mode='w', suffix=filename, delete=False) as f:
                f.write(content)
                original_file = f.name
            
            try:
                # Convert file to base64
                base64_content = file_to_base64(original_file)
                print(f"  ✓ File converted to base64 (length: {len(base64_content)})")
                
                # Convert base64 back to file
                new_file = original_file + ".copy"
                base64_to_file(base64_content, new_file)
                print(f"  ✓ Base64 converted back to file")
                
                # Verify integrity
                original_hash = self.calculate_file_hash(original_file)
                new_hash = self.calculate_file_hash(new_file)
                
                files_match = original_hash == new_hash
                print(f"  ✓ File integrity: {files_match}")
                
                # Verify content
                with open(new_file, 'r', encoding='utf-8') as f:
                    new_content = f.read()
                
                content_match = content == new_content
                print(f"  ✓ Content integrity: {content_match}")
                
                assert files_match, f"File hashes don't match for {filename}"
                assert content_match, f"Content doesn't match for {filename}"
                
                os.unlink(new_file)
                
            finally:
                os.unlink(original_file)

    def test_mixed_file_types(self):
        """Test various file types to ensure proper handling."""
        print("\n=== Testing Mixed File Types ===")
        
        test_cases = [
            # (filename, content, expected_encoding, expected_mime_type)
            ("script.py", "print('Hello, World!')", "text", "text/x-python"),
            ("data.json", '{"test": "data"}', "text", "application/json"),
            ("config.yaml", "key: value\nlist:\n  - item1\n  - item2", "text", "application/x-yaml"),
            ("document.txt", "Plain text document", "text", "text/plain"),
            ("image.png", b'\x89PNG\r\n\x1a\n', "base64", "image/png"),
            ("archive.zip", b'PK\x03\x04', "base64", "application/zip"),
            ("video.mp4", b'\x00\x00\x00\x20ftypmp4', "base64", "video/mp4"),
        ]
        
        for filename, content, expected_encoding, expected_mime in test_cases:
            print(f"\nTesting {filename}:")
            
            # Create test file
            mode = 'wb' if isinstance(content, bytes) else 'w'
            with tempfile.NamedTemporaryFile(mode=mode, suffix=filename, delete=False) as f:
                f.write(content)
                test_file = f.name
            
            try:
                # Test file reading
                file_info = read_file(test_file)
                
                # Verify encoding
                encoding_match = file_info['encoding'] == expected_encoding
                print(f"  ✓ Encoding: {file_info['encoding']} (expected: {expected_encoding}) - {encoding_match}")
                
                # Verify MIME type (approximate)
                mime_match = expected_mime in file_info['mime_type'] or file_info['mime_type'] in expected_mime
                print(f"  ✓ MIME type: {file_info['mime_type']} (expected: {expected_mime}) - {mime_match}")
                
                # Test file type detection
                is_text = is_text_file(test_file)
                is_binary = is_binary_file(test_file)
                print(f"  ✓ Type detection: text={is_text}, binary={is_binary}")
                
                # Verify type detection matches encoding
                type_match = (is_text and expected_encoding == "text") or (is_binary and expected_encoding == "base64")
                print(f"  ✓ Type detection match: {type_match}")
                
                assert encoding_match, f"Encoding mismatch for {filename}"
                assert type_match, f"Type detection mismatch for {filename}"
                
            finally:
                os.unlink(test_file)

    def test_error_handling(self):
        """Test error handling for edge cases."""
        print("\n=== Testing Error Handling ===")
        
        # Test 1: Non-existent file
        try:
            read_file("non_existent_file.txt")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            print("✓ Correctly handled non-existent file")
        
        # Test 2: Invalid base64
        try:
            base64_to_text("invalid_base64_content!")
            assert False, "Should have raised exception for invalid base64"
        except Exception as e:
            print(f"✓ Correctly handled invalid base64: {type(e).__name__}")
        
        # Test 3: Large file (create a file larger than default limit)
        large_content = "x" * (51 * 1024 * 1024)  # 51MB
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(large_content)
            large_file = f.name
        
        try:
            try:
                read_file(large_file)
                assert False, "Should have raised ValueError for large file"
            except ValueError as e:
                print(f"✓ Correctly handled large file: {e}")
        finally:
            os.unlink(large_file)

    
if __name__ == "__main__":
    unittest.main()