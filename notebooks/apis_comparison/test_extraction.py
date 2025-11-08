#!/usr/bin/env python3
"""
Test script to verify function extraction works correctly.
"""

import ast
import sys
from pathlib import Path

def extract_functions_from_file(file_path: str):
    """Extract all function definitions from a Python file."""
    functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else find_function_end(lines, start_line)
                
                # Extract function code
                function_code = '\n'.join(lines[start_line:end_line])
                
                # Extract function signature
                signature = get_function_signature(node)
                
                # Extract docstring
                docstring = ast.get_docstring(node)
                
                functions.append({
                    'name': node.name,
                    'signature': signature,
                    'code': function_code,
                    'docstring': docstring or "",
                    'start_line': start_line + 1,
                    'end_line': end_line,
                    'file_path': file_path
                })
                
    except Exception as e:
        print(f"⚠️ Error parsing file {file_path}: {e}")
    
    return functions

def get_function_signature(node: ast.FunctionDef) -> str:
    """Extract function signature from AST node."""
    try:
        args = []
        
        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        # *args
        if node.args.vararg:
            vararg_str = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg_str += f": {ast.unparse(node.args.vararg.annotation)}"
            args.append(vararg_str)
        
        # **kwargs
        if node.args.kwarg:
            kwarg_str = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg_str += f": {ast.unparse(node.args.kwarg.annotation)}"
            args.append(kwarg_str)
        
        # Return type annotation
        return_annotation = ""
        if node.returns:
            return_annotation = f" -> {ast.unparse(node.returns)}"
        
        return f"{node.name}({', '.join(args)}){return_annotation}"
        
    except Exception as e:
        return f"{node.name}(...)"

def find_function_end(lines, start_line):
    """Find the end line of a function by analyzing indentation."""
    if start_line >= len(lines):
        return start_line + 1
    
    func_line = lines[start_line]
    base_indent = len(func_line) - len(func_line.lstrip())
    
    end_line = start_line + 1
    while end_line < len(lines):
        line = lines[end_line]
        
        if line.strip() == "":
            end_line += 1
            continue
        
        line_indent = len(line) - len(line.lstrip())
        if line_indent <= base_indent:
            break
        
        end_line += 1
    
    return end_line

def test_single_file(file_path: str):
    """Test function extraction on a single file."""
    print(f"\n📄 Testing file: {file_path}")
    print("=" * 60)
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return
    
    functions = extract_functions_from_file(file_path)
    
    if not functions:
        print("⚠️ No functions found in this file")
        return
    
    print(f"✅ Found {len(functions)} functions:")
    
    for i, func in enumerate(functions, 1):
        print(f"\n{i}. {func['name']}")
        print(f"   📝 Signature: {func['signature']}")
        print(f"   📍 Lines: {func['start_line']}-{func['end_line']}")
        print(f"   📄 Code preview: {func['code'][:100]}...")
        if func['docstring']:
            print(f"   📚 Docstring: {func['docstring'][:100]}...")

def test_version_directory(version_path: str):
    """Test function extraction on a version directory."""
    print(f"\n📁 Testing version directory: {version_path}")
    print("=" * 60)
    
    version_dir = Path(version_path)
    if not version_dir.exists():
        print(f"❌ Directory not found: {version_path}")
        return
    
    total_functions = 0
    api_count = 0
    
    # Process each API directory
    for api_dir in version_dir.iterdir():
        if not api_dir.is_dir():
            continue
        
        api_count += 1
        api_functions = 0
        
        print(f"\n📋 API: {api_dir.name}")
        
        # Scan all Python files in the API directory
        for py_file in api_dir.rglob("*.py"):
            # Skip certain directories
            if any(skip in str(py_file) for skip in ["SimulationEngine", "tests", "__pycache__"]):
                continue
            
            functions = extract_functions_from_file(str(py_file))
            
            if functions:
                relative_path = py_file.relative_to(api_dir)
                print(f"   📝 {relative_path}: {len(functions)} functions")
                api_functions += len(functions)
        
        print(f"   📊 Total functions in {api_dir.name}: {api_functions}")
        total_functions += api_functions
    
    print(f"\n📊 SUMMARY:")
    print(f"   APIs processed: {api_count}")
    print(f"   Total functions: {total_functions}")
    print(f"   Average functions per API: {total_functions / api_count if api_count > 0 else 0:.1f}")

def main():
    """Main function."""
    print("🧪 Function Extraction Test")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_extraction.py <file_path>       # Test single file")
        print("  python test_extraction.py <directory_path>  # Test directory")
        print("\nExamples:")
        print("  python test_extraction.py APIs_V0.0.1/cursor/cursorAPI.py")
        print("  python test_extraction.py APIs_V0.0.1")
        return
    
    path = sys.argv[1]
    path_obj = Path(path)
    
    if path_obj.is_file():
        test_single_file(path)
    elif path_obj.is_dir():
        test_version_directory(path)
    else:
        print(f"❌ Path not found: {path}")

if __name__ == "__main__":
    main() 