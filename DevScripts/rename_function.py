import os
import tokenize
import io

def replace_function_calls_in_file(file_path, func_mapping, import_mapping=None):
    """
    Replace function calls in a Python file according to func_mapping.
    Optionally, add import statements for new functions if import_mapping is provided.

    Args:
        file_path (str): Path to the Python file.
        func_mapping (dict): Mapping of old_func_name -> new_func_name.
        import_mapping (dict, optional): Mapping of new_func_name -> import_statement (with \n).
    """
    with open(file_path, 'rb') as f:
        source_bytes = f.read()

    encoding = tokenize.detect_encoding(io.BytesIO(source_bytes).readline)[0]
    source = source_bytes.decode(encoding)

    modified = False
    tokens = []
    g = tokenize.tokenize(io.BytesIO(source_bytes).readline)
    prev_token = None
    for tok in g:
        toknum, tokval, start, end, line = tok.type, tok.string, tok.start, tok.end, tok.line
        # Replace only bare function calls, not attribute access (e.g., not obj.print())
        if (
            toknum == tokenize.NAME and tokval in func_mapping
            and prev_token is not None
            and not (prev_token.type == tokenize.OP and prev_token.string == '.')
        ):
            tokens.append(tok)
            try:
                next_token = next(g)
            except StopIteration:
                break
            if next_token.type == tokenize.OP and next_token.string == '(':
                # Replace function name
                last_tok = tokens[-1]
                new_func = func_mapping[tokval]
                tokens[-1] = tokenize.TokenInfo(
                    last_tok.type, new_func, last_tok.start, last_tok.end, last_tok.line
                )
                modified = True
            tokens.append(next_token)
            prev_token = next_token
            continue
        tokens.append(tok)
        prev_token = tok

    if not modified:
        return False

    new_source = tokenize.untokenize(tokens)
    if isinstance(new_source, bytes):
        new_source = new_source.decode(encoding)

    # Insert import statements if needed
    if import_mapping:
        lines = new_source.splitlines(keepends=True)
        for new_func, import_stmt in import_mapping.items():
            if new_func in func_mapping.values():
                if not any(line.strip() == import_stmt.strip() for line in lines):
                    # Insert after any __future__ imports or at the top
                    insert_idx = 0
                    for i, line in enumerate(lines):
                        if line.startswith('from __future__') or line.startswith('import __future__'):
                            insert_idx = i + 1
                    lines.insert(insert_idx, import_stmt)
        new_source = ''.join(lines)

    with open(file_path, 'wb') as f:
        f.write(new_source.encode(encoding))
    return True

def replace_functions_in_dir(root_folder, func_mapping, import_mapping=None, ignore_dirs=('tests', '.vscode')):
    """
    Recursively replace function calls in all .py files under root_folder.

    Args:
        root_folder (str): Directory to search.
        func_mapping (dict): Mapping of old_func_name -> new_func_name.
        import_mapping (dict, optional): Mapping of new_func_name -> import_statement (with \n).
        ignore_dirs (tuple): Directory names to ignore.
    """
    for dirpath, dirnames, filenames in os.walk(root_folder):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        for filename in filenames:
            if filename.endswith('.py'):
                file_path = os.path.join(dirpath, filename)
                replace_function_calls_in_file(file_path, func_mapping, import_mapping)

# Example usage:
# To replace 'print' with 'print_log' and add the import if needed:
if __name__ == "__main__":
    func_mapping = {'print': 'print_log'}
    import_mapping = {'print_log': 'from common_utils.print_log import print_log\n'}
    replace_functions_in_dir('APIs', func_mapping, import_mapping)
