import ast
import os
import re


###### Chunk Schema ######
# {
#     "file_path": str,    # Absolute path to the file
#     "language": str,     # Detected language (e.g., "python", "markdown", "text")
#     "chunk_type": str,   # Type of chunk (e.g., "function", "class", "heading", "paragraph", "code_block")
#     "content": str,      # The actual text content of the chunk
#     "start_line": int,   # 1-indexed starting line number in the original file
#     "end_line": int,     # 1-indexed ending line number in the original file
#     "metadata": dict      # Optional dictionary for type-specific metadata (e.g., function name, heading level)
# }


def get_language_from_path(file_path):
    """Determines the language from the file extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext == ".py":
        return "python"
    elif ext == ".md":
        return "markdown"
    elif ext in [
        ".txt",
        ".log",
        ".csv",
        ".xml",
        ".json",
        ".yaml",
        ".yml",
    ]:  # Add more plain text types
        return "text"
    # Add more languages as needed:
    # elif ext in [".js", ".jsx"]: return "javascript"
    # elif ext in [".ts", ".tsx"]: return "typescript"
    # elif ext == ".java": return "java"
    # elif ext == ".html": return "html"
    # elif ext == ".css": return "css"
    else:
        # For unknown extensions, decide whether to treat as "text" or skip
        return "text"  # Default to generic text chunking for unknown types


def chunk_python_file(file_path, content_lines):
    """Chunks a Python file using its AST."""
    source = "".join(content_lines)
    chunks = []

    try:
        module = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        # If syntax error, create a single chunk for the whole file with error info
        chunks.append(
            {
                "file_path": file_path,
                "language": "python",
                "chunk_type": "file_with_syntax_error",
                "content": source,
                "start_line": 1,
                "end_line": len(content_lines) if content_lines else 1,
                "metadata": {
                    "error_message": str(e),
                    "error_line": e.lineno,
                    "error_offset": e.offset,
                },
            }
        )
        return chunks

    for node in module.body:
        start_line = node.lineno
        end_line = getattr(
            node, "end_lineno", start_line
        )  # Requires Python 3.8+ for wide availability

        node_content_lines = content_lines[start_line - 1 : end_line]
        node_content = "".join(node_content_lines)

        chunk_type = "module_statement"  # Default for top-level statements
        metadata = {}

        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            chunk_type = (
                "function" if isinstance(node, ast.FunctionDef) else "async_function"
            )
            metadata["name"] = node.name
            metadata["args"] = [arg.arg for arg in node.args.args]
            if node.returns:
                if hasattr(ast, "unparse"):  # Python 3.9+
                    try:
                        metadata["returns"] = ast.unparse(node.returns)
                    except:
                        metadata["returns"] = "complex_annotation"
                elif isinstance(node.returns, ast.Name):
                    metadata["returns"] = node.returns.id
                elif isinstance(node.returns, ast.Constant) and isinstance(
                    node.returns.value, str
                ):
                    metadata["returns"] = node.returns.value

        elif isinstance(node, ast.ClassDef):
            chunk_type = "class"
            metadata["name"] = node.name
            metadata["bases"] = []
            for base in node.bases:
                if hasattr(ast, "unparse"):
                    try:
                        metadata["bases"].append(ast.unparse(base))
                    except:
                        metadata["bases"].append("complex_base")
                elif isinstance(base, ast.Name):
                    metadata["bases"].append(base.id)
            # You could recursively chunk methods and inner classes here if desired
            # For this version, the class body is part of the class chunk's content

        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            chunk_type = "import_statement"
            if isinstance(node, ast.Import):
                metadata["imports"] = [
                    {"name": alias.name, "asname": alias.asname} for alias in node.names
                ]
            else:  # ast.ImportFrom
                metadata["module"] = node.module if node.module else "." * node.level
                metadata["imports"] = [
                    {"name": alias.name, "asname": alias.asname} for alias in node.names
                ]

        elif isinstance(node, ast.If):
            chunk_type = "if_block"
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            chunk_type = "for_loop"
        elif isinstance(node, ast.While):
            chunk_type = "while_loop"
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            chunk_type = "with_block"
        elif isinstance(node, ast.Try):
            chunk_type = "try_block"

        elif isinstance(node, ast.Assign):
            chunk_type = "assignment"
            metadata["targets"] = []
            for target in node.targets:
                if hasattr(ast, "unparse"):
                    try:
                        metadata["targets"].append(ast.unparse(target))
                    except:
                        metadata["targets"].append("complex_target")
                elif isinstance(target, ast.Name):
                    metadata["targets"].append(target.id)

        elif (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            # Check if it's the module docstring
            if (
                module.body.index(node) == 0
                and ast.get_docstring(module, clean=False) == node.value.value
            ):
                chunk_type = "module_docstring"
                metadata["docstring"] = node.value.value
            else:
                chunk_type = "expression_statement"  # e.g. a string literal on its own

        # For other types, default "module_statement" is used.

        # Ensure content is not just whitespace before adding, or always add
        # We strip trailing newlines for consistency
        stripped_content = node_content.rstrip(
            "\n"
        )  # Prefer rstrip to keep internal structure

        if stripped_content or chunk_type in [
            "module_docstring",
            "function",
            "class",
        ]:  # Keep important structures even if "empty"
            chunks.append(
                {
                    "file_path": file_path,
                    "language": "python",
                    "chunk_type": chunk_type,
                    "content": stripped_content,
                    "start_line": start_line,
                    "end_line": end_line,
                    "metadata": metadata,
                }
            )
    return chunks


def chunk_markdown_file(file_path, content_lines):
    """Chunks a Markdown file using heuristics (headings, code blocks, paragraphs)."""
    chunks = []
    current_paragraph_lines = []
    current_paragraph_start_line = 0
    in_code_block = False
    code_block_lines = []
    code_block_start_line = 0
    code_block_lang = ""

    # Add a sentinel empty line to help process the last paragraph/block
    effective_content_lines = content_lines + [""]

    for i, line_content in enumerate(effective_content_lines):
        line_num = i + 1  # 1-indexed
        stripped_line = line_content.strip()

        if stripped_line.startswith("```"):
            if not in_code_block:  # Start of code block
                # Finalize previous paragraph if any
                if current_paragraph_lines:
                    chunks.append(
                        {
                            "file_path": file_path,
                            "language": "markdown",
                            "chunk_type": "paragraph",
                            "content": "".join(current_paragraph_lines).rstrip("\n"),
                            "start_line": current_paragraph_start_line,
                            "end_line": line_num - 1,
                            "metadata": {},
                        }
                    )
                    current_paragraph_lines = []

                in_code_block = True
                code_block_start_line = line_num
                code_block_lang_match = re.match(r"```(\w+)?", stripped_line)
                code_block_lang = (
                    code_block_lang_match.group(1)
                    if code_block_lang_match and code_block_lang_match.group(1)
                    else ""
                )
                code_block_lines.append(line_content)
            else:  # End of code block
                code_block_lines.append(line_content)
                chunks.append(
                    {
                        "file_path": file_path,
                        "language": "markdown",
                        "chunk_type": "code_block",
                        "content": "".join(code_block_lines).rstrip("\n"),
                        "start_line": code_block_start_line,
                        "end_line": line_num,
                        "metadata": {"language": code_block_lang},
                    }
                )
                code_block_lines = []
                in_code_block = False
        elif in_code_block:
            code_block_lines.append(line_content)
        elif stripped_line.startswith("#"):
            if current_paragraph_lines:  # Finalize previous paragraph
                chunks.append(
                    {
                        "file_path": file_path,
                        "language": "markdown",
                        "chunk_type": "paragraph",
                        "content": "".join(current_paragraph_lines).rstrip("\n"),
                        "start_line": current_paragraph_start_line,
                        "end_line": line_num - 1,
                        "metadata": {},
                    }
                )
                current_paragraph_lines = []

            heading_text = stripped_line.lstrip("#").strip()
            level = len(stripped_line.split(" ", 1)[0])  # Count of '#'
            chunks.append(
                {
                    "file_path": file_path,
                    "language": "markdown",
                    "chunk_type": "heading",
                    "content": stripped_line,  # Store the line with '#'
                    "start_line": line_num,
                    "end_line": line_num,
                    "metadata": {"text": heading_text, "level": level},
                }
            )
        elif (
            stripped_line
        ):  # Non-empty line, not a heading or code fence (when not in code block)
            if not current_paragraph_lines:
                current_paragraph_start_line = line_num
            current_paragraph_lines.append(line_content)
        else:  # Empty line (and not in code block)
            if current_paragraph_lines:
                chunks.append(
                    {
                        "file_path": file_path,
                        "language": "markdown",
                        "chunk_type": "paragraph",
                        "content": "".join(current_paragraph_lines).rstrip("\n"),
                        "start_line": current_paragraph_start_line,
                        "end_line": line_num - 1,
                        "metadata": {},
                    }
                )
                current_paragraph_lines = []

    # Note: The sentinel line handles the last paragraph. If an unterminated code block exists
    # at EOF, it won't be added by this logic. A more robust solution might handle that.
    if in_code_block and code_block_lines:  # Handle unterminated code block at EOF
        chunks.append(
            {
                "file_path": file_path,
                "language": "markdown",
                "chunk_type": "code_block",
                "content": "".join(code_block_lines).rstrip("\n"),
                "start_line": code_block_start_line,
                "end_line": len(content_lines),  # Ends at last line of actual content
                "metadata": {"language": code_block_lang, "unterminated": True},
            }
        )

    return chunks


def chunk_generic_file(file_path, content_lines, language="text"):
    """Chunks a generic text file by paragraphs (blocks separated by empty lines)."""
    chunks = []
    current_paragraph_lines = []
    current_paragraph_start_line = 0

    # Add a sentinel empty line to help process the last paragraph
    effective_content_lines = content_lines + [""]

    for i, line_content in enumerate(effective_content_lines):
        line_num = i + 1  # 1-indexed
        stripped_line = line_content.strip()

        if stripped_line:  # Non-empty line
            if not current_paragraph_lines:
                current_paragraph_start_line = line_num
            current_paragraph_lines.append(line_content)
        else:  # Empty line
            if current_paragraph_lines:
                chunks.append(
                    {
                        "file_path": file_path,
                        "language": language,
                        "chunk_type": "paragraph",
                        "content": "".join(current_paragraph_lines).rstrip("\n"),
                        "start_line": current_paragraph_start_line,
                        "end_line": line_num - 1,
                        "metadata": {},
                    }
                )
                current_paragraph_lines = []

    return chunks


def chunk_codebase(db):
    """
    Processes the in-memory DB to chunk all files.
    """
    all_chunks = []
    if not db or "file_system" not in db:
        return all_chunks

    for file_path, file_data in db["file_system"].items():
        if (
            not file_data["is_directory"] and file_data["content_lines"]
        ):  # Process non-empty files
            language = get_language_from_path(file_path)
            content_lines = file_data["content_lines"]

            if not content_lines:  # Skip empty files
                continue

            file_chunks = []
            if language == "python":
                file_chunks = chunk_python_file(file_path, content_lines)
            elif language == "markdown":
                file_chunks = chunk_markdown_file(file_path, content_lines)
            elif language == "text":  # or any other language to be treated as generic
                file_chunks = chunk_generic_file(
                    file_path, content_lines, language=language
                )
            # Add elif for other specific language chunkers here
            else:  # Fallback for other known but not specifically handled languages
                file_chunks = chunk_generic_file(
                    file_path, content_lines, language=language
                )

            all_chunks.extend(file_chunks)
        elif not file_data["is_directory"] and not file_data["content_lines"]:
            # Optionally create a specific chunk for empty files if needed for some reason
            pass  # print(f"Skipping empty file: {file_path}")

    return all_chunks
