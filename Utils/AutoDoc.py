#%%
import os
import ast
import re
import docspec
from pprint import pprint
from typing import List, Tuple, Dict, Any, Generator
from pydoc_markdown import Context, PythonLoader, MarkdownRenderer
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import json


## Step 1
def replace_function_names_with_flat_counterpart(module, function_map):
    """Replace function names with flattened function names.
    
    Args:
        module (str): The pydoc markdown module wise state dictionary
        function_map (dict): A dictionary mapping flattened function names to their original fully qualified function names.
    """

    invert_function_map = lambda f_map: {v:k for k, v in f_map.items()}
    filter_function_map = lambda f_map, module_name: {k:v for k, v in f_map.items() if k.startswith(module_name)}
    remove_module_nesting_from_funcmap = lambda f_map: {k.split(".")[-1]:v for k, v in f_map.items()}

    converted_function_map = remove_module_nesting_from_funcmap(filter_function_map(invert_function_map(function_map), module.name))

    # Keep only mapped members
    filtered_members = []
    for member in module.members:
        if "Function(" not in str(member):
            continue
        if member.name not in converted_function_map:
            # print(f"🟡 Skipping unmapped function: {member.name}")
            continue

        # Rename the function and keep it
        member.name = converted_function_map[member.name]
        filtered_members.append(member)

    # Overwrite the module's members with only those that are mapped
    module.members = filtered_members

# --- Recursive Helper Function (Processes, Filters, and Renames) ---
def _recursively_process_and_filter_members(
    current_members: List[docspec.ApiObject],
    current_path_prefix: str,
    service_wide_inverted_map: Dict[str, str]  # Map of {FQN: FlatName} for the entire service
) -> List[docspec.ApiObject]: # Returns the new, filtered list of members
    """
    Recursively traverses API objects, renames functions/methods, and filters members.
    Only mapped functions/methods are kept. Classes are kept if they still contain
    members after recursive filtering. Other member types are dropped.

    Args:
        current_members: List of API objects to process.
        current_path_prefix: FQN prefix for the current scope.
        service_wide_inverted_map: {FQN: FlatName} map for the service.

    Returns:
        A new list of docspec.ApiObject members that have been processed and filtered.
    """
    new_filtered_members_list: List[docspec.ApiObject] = []
    num_prefix_parts = len(current_path_prefix.split('.'))

    # Build a map for resolving flat names for direct members at this level
    simple_name_to_flat_name_map_for_current_level: Dict[str, str] = {}
    for fqn, flat_name in service_wide_inverted_map.items():
        if fqn.startswith(current_path_prefix + "."):
            fqn_parts = fqn.split('.')
            if len(fqn_parts) == num_prefix_parts + 1: # Direct child
                original_simple_name = fqn_parts[-1]
                simple_name_to_flat_name_map_for_current_level[original_simple_name] = flat_name

    for member in current_members:
        if isinstance(member, docspec.Function):
            if member.name in simple_name_to_flat_name_map_for_current_level:
                member.name = simple_name_to_flat_name_map_for_current_level[member.name]
                new_filtered_members_list.append(member) # Keep renamed function
            # else: unmapped function is dropped (not added to new_filtered_members_list)

        elif isinstance(member, docspec.Class):
            class_fqn_prefix = current_path_prefix + "." + member.name
            
            # Recursively process and filter the class's members
            filtered_class_members = _recursively_process_and_filter_members(
                member.members,
                class_fqn_prefix,
                service_wide_inverted_map
            )
            member.members = filtered_class_members # Update the class with its (potentially empty) filtered members

            # Keep the class if it still has members after its own members were filtered
            if member.members:
                new_filtered_members_list.append(member)
            # else: class with no mapped/kept methods is dropped

        # Other ApiObject types (Variables, nested Modules not handled by outer loop, etc.)
        # are implicitly dropped as they are not explicitly added to new_filtered_members_list.
        # This aligns with the original code's behavior of primarily keeping only mapped "Functions".

    return new_filtered_members_list


def insert_flat_function_names(
        modules_generator: Generator[docspec.Module, None, None],
        servicewise_function_map_dictionaries: Dict[str, Dict[str, str]],
    ) -> None:
    """
    Processes docspec.Module objects:
    1. Filters modules (e.g., removing tests).
    2. For each remaining module, recursively processes its members:
        - Renames functions and methods found in `servicewise_function_map_dictionaries` to their flat names.
        - Filters out functions/methods not found in the map.
        - Filters out classes that, after this process, contain no mapped/renamed methods.
        - Other member types (like variables) are effectively filtered out.
    The `members` attribute of each processed `docspec.Module` object is updated in place.

    Args:
        modules_generator: Generator of top-level docspec.Module objects from pydoc.
        servicewise_function_map_dictionaries: Dict of {service_name: {flat_name: FQN}}.
    """
    _MODULE_EXCLUDE_PATTERNS = {".tests"} # Define or import appropriately

    def filter_excluded_modules_internal(
        module_gen: Generator[docspec.Module, None, None]
    ) -> List[docspec.Module]:
        return [
            mod for mod in module_gen
            if not any(pattern in mod.name for pattern in _MODULE_EXCLUDE_PATTERNS)
        ]

    def get_top_level_names_internal(
        module_list_arg: List[docspec.Module]
    ) -> List[str]:
        return list(set(module.name.split(".")[0] for module in module_list_arg))

    module_list: List[docspec.Module] = filter_excluded_modules_internal(modules_generator)
    top_level_service_names: List[str] = get_top_level_names_internal(module_list)

    module_wise_dict: Dict[str, List[docspec.Module]] = {k: [] for k in top_level_service_names}
    for module_spec in module_list:
        service_name_key = module_spec.name.split(".")[0]
        if service_name_key in module_wise_dict:
            module_wise_dict[service_name_key].append(module_spec)

    for service_name in top_level_service_names:
        if service_name not in module_wise_dict or service_name not in servicewise_function_map_dictionaries:
            continue

        modules_for_this_service: List[docspec.Module] = module_wise_dict[service_name]
        current_service_flat_to_fqn_map: Dict[str, str] = servicewise_function_map_dictionaries[service_name]

        if not current_service_flat_to_fqn_map:
            continue

        current_service_fqn_to_flat_map: Dict[str, str] = {
            v: k for k, v in current_service_flat_to_fqn_map.items()
        }

        for module_spec_object in modules_for_this_service:
            # The recursive call now returns the new filtered list of members for the module
            new_module_members = _recursively_process_and_filter_members(
                module_spec_object.members,
                module_spec_object.name,
                current_service_fqn_to_flat_map
            )
            # Update the module's members list with the filtered and processed one
            module_spec_object.members = new_module_members

def convert_py_to_md_with_pydoc(source_folder: str, output_folder: str):
    """
    Converts Python files in the source folder to markdown documentation in the output folder using pydoc_markdown.

    Args:
    - source_folder (str): Path to the folder containing .py files.
    - output_folder (str): Path to the folder where the generated .md files will be saved.
    """
    # List of files to exclude from conversion (by filename)
    exclude_files = { 'db.py', 'init.py', '__init__.py'}

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Set up context for pydoc_markdown
    context = Context(directory=source_folder)

    # Initialize loader and renderer for generating markdown
    if os.path.exists(source_folder):
        abs_source_folder = os.path.abspath(source_folder)

    loader = PythonLoader(search_path=[abs_source_folder])  # Load from the provided source folder
    renderer = MarkdownRenderer(render_module_header=False)

    # Initialize the components
    loader.init(context)
    renderer.init(context)

    # Get all Python files in the source folder (excluding excluded ones)
    python_files = [f for f in os.listdir(source_folder) if f.endswith('.py') and f not in exclude_files]

    # Load the Python modules (files) from the filtered list
    modules = loader.load()

    filter_tests_and_simulation_engine = lambda module_generator_obj: list(filter(lambda x: ".tests" not in x.name, module_generator_obj))

    get_all_top_level_module_names_from_module_list = lambda modules: list(set([module.name.split(".")[0] for module in modules]))

    module_list = filter_tests_and_simulation_engine(modules)

    module_names = get_all_top_level_module_names_from_module_list(module_list)

    module_wise_dict = {k:[] for k in module_names}

    for module in module_list:
        module_wise_dict[module.name.split(".")[0]].append(module)

    return module_wise_dict

def extract_function_map_from_init(init_path: str) -> dict:
    """
    Extracts _function_map from a module's __init__.py using AST.

    Args:
        init_path (str): Path to the __init__.py file.

    Returns:
        dict: Flattened name -> fully qualified name
    """
    with open(init_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "_function_map":
                        return ast.literal_eval(ast.unparse(node.value))  # Python 3.9+
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                if node.target.id == "_function_map":
                    return ast.literal_eval(ast.unparse(node.value))
    return {}

def extract_utils_map_from_init(init_path: str) -> dict:
    """
    Extracts _utils_map from a module's __init__.py using AST.

    Args:
        init_path (str): Path to the __init__.py file.

    Returns:
        dict: Flattened name -> fully qualified name
    """
    with open(init_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "_utils_map":
                        return ast.literal_eval(ast.unparse(node.value))  # Python 3.9+
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                if node.target.id == "_utils_map":
                    return ast.literal_eval(ast.unparse(node.value))
    return {}

def render_modules_to_markdown(modules) -> str:
    """
    Renders pydoc markdown for modules to a markdown formatted string.
    """
    # Explicitly remove module-level docstrings before rendering
    for module_spec in modules:
        if isinstance(module_spec, docspec.Module): # Ensure it's a Module object
            module_spec.docstring = None # Clear the module's own docstring
    renderer = MarkdownRenderer(render_module_header=False)
    renderer.init(Context(directory='.'))  # context is required, but path can be dummy
    return renderer.render_to_string(modules)

def _process_content(content: str, utils_map: Dict[str, str] = None) -> str:
    """
    Processes the content of a Markdown file,ensuring no consecutive empty lines remain,
    and explicitly removing lines containing 'save_state' or 'load_state'.
    Skips any text before first function. Adds (utils) prefix to function titles that come from utils_map.

    Args:
        content: The raw content of the Markdown file.
        utils_map: Dictionary mapping flattened function names to their fully qualified names from utils.

    Returns:
        The processed content as a string.
    """
    """
    Processes the raw Markdown content:
    - Removes anchor tags (<a>).
    - Removes lines with 'save_state' or 'load_state'.
    - Removes Class headers (lines starting with ##).
    - Removes consecutive empty lines.
    - Skips any text before the first function definition (identified by '### `Function').
    - Adds (utils) prefix to function titles that come from utils_map.
    """
    # 1. Remove anchor tags
    content = re.sub(r'<a\s+(?:id|name)="[^"]*">\s*</a>\n?', '', content, flags=re.IGNORECASE)

    lines = content.splitlines()
    processed_lines: List[str] = []
    
    # Matches '## Some Text' (typically class headers from pydoc-markdown)
    class_header_pattern = re.compile(r'^\s*##\s+.+$') 
    # Matches function headers like '#### function_name'
    function_header_pattern = re.compile(r'^\s*####\s+(.+)$')
    forbidden_strings = {"save_state", "save\_state", "load_state", "load\_state"}

    utils_function_names = set(utils_map.keys()) if utils_map else set()

    for line in lines:
        # Skip class headers and lines with forbidden strings
        if class_header_pattern.match(line):
            continue
        if any(fs in line for fs in forbidden_strings):
            continue
        
        # Check if this is a function header and if it's from utils_map
        function_match = function_header_pattern.match(line)
        if function_match and utils_function_names:
            function_name = function_match.group(1).strip()
            # Remove any escape characters for comparison
            clean_function_name = function_name.replace('\_', '_')
            if clean_function_name in utils_function_names:
                # Add (utils) prefix to the function title
                line = line.replace(f'#### {function_name}', f'#### (utils) {function_name}')
        
        processed_lines.append(line)

    # Remove consecutive empty lines
    final_lines: List[str] = []
    previous_was_empty = False
    for line in processed_lines:
        is_empty = not line.strip()
        if not is_empty or not previous_was_empty:
            final_lines.append(line)
        previous_was_empty = is_empty
    
    # Skip text before the first function signature (e.g., '### `FunctionName(...`')
    start_idx = 0
    # pydoc-markdown usually renders functions like: ### `function_name()`
    # Or ### `ClassName.method_name()`
    # The key is the pattern "### `"
    function_signature_pattern = re.compile(r'^\s*###\s+`.*`') 
    for i, line in enumerate(final_lines):
        if function_signature_pattern.match(line.strip()):
            start_idx = i
            break
    return "\n".join(final_lines[start_idx:])

## Filtering Pass Functions (Functions with pass in their code)
def resolve_function_source_path(qualified: str, source_root: str) -> str:
    """
    Convert a qualified path (e.g., 'my_package.my_module.my_function') to a file path
    and return the .py file containing the function.
    """
    parts = qualified.split(".")
    # The last part is the function/class name, the preceding parts form the module path.
    *module_parts, _ = parts
    base_path = os.path.join(source_root, *module_parts)

    module_file = base_path + ".py"
    if os.path.isfile(module_file):
        return module_file
    elif os.path.isdir(base_path):
        # Check for package __init__.py
        init_file = os.path.join(base_path, "__init__.py")
        if os.path.isfile(init_file):
            return init_file
    # Providing more details in the error message for better debugging
    raise FileNotFoundError(f"Could not resolve source file for {qualified}. Tried: '{module_file}' and '{init_file if 'init_file' in locals() else 'N/A'}'")

def strip_comments(source: str) -> str:
    """
    Strip comments from a Python source code string.
    Removes lines that are entirely comments or inline comments from the end of lines.
    """
    lines = source.splitlines()
    no_comment_lines = []
    for line in lines:
        # Remove everything from '#' to the end of the line
        no_comment = re.sub(r'#.*', '', line)
        # Keep only non-empty lines after stripping comments and whitespace
        if no_comment.strip():
            no_comment_lines.append(no_comment)
    return '\n'.join(no_comment_lines)

def strip_comments_and_docstrings(source: str) -> str:
    """
    Strip comments and docstrings from a Python source code string.
    This version improves docstring removal by precisely identifying docstring
    line ranges via AST (using `lineno` and `end_lineno`) and then reconstructing
    the source without those lines. It ensures that only actual docstring content
    is removed without affecting identical strings elsewhere in the code.
    It then applies `strip_comments` to handle remaining comments.
    """
    try:
        parsed = ast.parse(source)
    except Exception: # Catching broad exception for resilience against syntax errors
        # If parsing fails, fall back to just stripping comments
        return strip_comments(source)

    lines = source.splitlines()
    lines_to_exclude = set()

    for node in ast.walk(parsed):
        # Check for nodes that can contain docstrings
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            # Docstring is typically the first statement in the body
            if hasattr(node, 'body') and len(node.body) > 0:
                doc_node = node.body[0]
                # Verify it's an AST expression node containing a string constant (the docstring itself)
                if isinstance(doc_node, ast.Expr) and isinstance(doc_node.value, ast.Constant) and isinstance(doc_node.value.value, str):
                    # Mark all lines occupied by the docstring for exclusion
                    # `ast.lineno` and `ast.end_lineno` are 1-based, so adjust to 0-based for list indexing
                    start_line = doc_node.lineno - 1
                    end_line = doc_node.end_lineno - 1 # `end_lineno` available since Python 3.8+
                    
                    for i in range(start_line, end_line + 1):
                        lines_to_exclude.add(i)

    # Reconstruct the source without docstring lines
    filtered_lines = []
    for i, line in enumerate(lines):
        if i not in lines_to_exclude:
            filtered_lines.append(line)
            
    # Join the lines and then strip any remaining comments
    return strip_comments('\n'.join(filtered_lines))

def extract_function_source(source: str, func_path: str) -> str:
    """
    Extracts the source code for a function or method from the full module source.
    `func_path` can be: 'function_name' or 'ClassName.method_name'.
    """
    tree = ast.parse(source)

    if "." in func_path:
        class_name, method_name = func_path.split(".")
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for sub_node in node.body:
                    if isinstance(sub_node, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub_node.name == method_name:
                        # ast.get_source_segment requires the original source string
                        return ast.get_source_segment(source, sub_node)
    else:
        # Top-level function
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_path:
                # ast.get_source_segment requires the original source string
                return ast.get_source_segment(source, node)

    raise ValueError(f"Function or method '{func_path}' not found in source.")

# --- Helper Functions for Triviality Check ---

def is_node_trivial_return(node: ast.stmt) -> bool:
    """
    Checks if an AST node represents a trivial return statement (e.g., `return`, `return None`,
    `return []`, `return {}`, `return 0`, `return ""`).
    """
    if not isinstance(node, ast.Return):
        return False

    value = node.value
    if value is None:
        return True  # `return` (without a value)

    if isinstance(value, ast.Constant):
        # Check for `None`, empty string, empty bytes, zero (int/float), `False`
        if value.value is None: return True
        if isinstance(value.value, (str, bytes)) and not value.value: return True
        if isinstance(value.value, (int, float)) and value.value == 0: return True
        if isinstance(value.value, bool) and not value.value: return True # `False`
    elif isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        # Check for empty lists, tuples, sets
        if not value.elts: return True
    elif isinstance(value, ast.Dict):
        # Check for empty dictionaries
        if not value.keys: return True
    elif isinstance(value, ast.Name) and value.id == 'None':
        # For older Python versions or specific contexts where `None` might be a `Name` node
        return True
    return False

def is_function_body_trivial(func_source_code: str) -> bool:
    """
    Analyzes the extracted source code of a single function to determine if its body is trivial.
    Trivial bodies include:
    - Only a `pass` statement.
    - Only a `return` statement (with or without a value, including empty literals).
    - An empty body after stripping comments and docstrings.

    Args:
        func_source_code (str): The full source code of a single function (including `def ...:`).
    Returns:
        bool: True if the function body is considered trivial, False otherwise.
    """
    # First, strip comments and docstrings from the function's source.
    stripped_func_source = strip_comments_and_docstrings(func_source_code)

    # If the stripped source is empty or contains only whitespace, it's trivial.
    if not stripped_func_source.strip():
        return True

    try:
        # Parse the stripped function source. It should contain a single function definition.
        tree = ast.parse(stripped_func_source)
    except SyntaxError:
        # If the stripped source is malformed (e.g., due to aggressive stripping),
        # it's safer to assume it's not trivial to avoid false positives.
        return False
    except Exception as e:
        print(f"⚠️ An unexpected error occurred during AST parsing for triviality check: {e}")
        return False

    # The AST should contain one top-level FunctionDef or AsyncFunctionDef node.
    function_node = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_node = node
            break

    if not function_node:
        # This indicates that the parsed `func_source_code` did not yield a function definition.
        return False # If not a function definition, it's not a "trivial function body".

    # Get the statements within the function's body.
    function_body_statements = function_node.body

    # Filter out any `Expr` nodes that are just string literals (e.g., remaining docstrings
    # or standalone strings). These should not count as "functional" code for triviality.
    effective_statements = []
    for stmt in function_body_statements:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            continue # Skip string literal expressions (like docstrings or standalone strings)
        effective_statements.append(stmt)

    # If the effective body is empty after filtering, the function is trivial.
    if not effective_statements:
        return True

    # If there is exactly one effective statement and it's `pass` or a trivial `return`.
    if len(effective_statements) == 1:
        stmt = effective_statements[0]
        if isinstance(stmt, ast.Pass):
            return True
        if is_node_trivial_return(stmt):
            return True

    return False

# --- Main Filtering Logic ---

def find_trivial_functions(fq_function_names: List[str], source_root: str) -> List[str]:
    """
    Find trivial functions by analyzing their stripped source code based on AST.
    Trivial functions include those with only 'pass', 'return', 'return None',
    'return []', 'return {}', 'return 0', 'return ""', etc. in their body.

    Args:
        fq_function_names (List[str]): A list of fully qualified function names (e.g., `my_module.my_function`, `my_module.MyClass.my_method`).
        source_root (str): The root directory for resolving fully qualified names.
    Returns:
        List[str]: A list of fully qualified function names that are considered trivial.
    """
    trivial_functions_list = []

    for fq in fq_function_names:
        try:
            file_path = resolve_function_source_path(fq, source_root)

            # Determine the function/method path relative to its module (e.g., 'my_function' or 'MyClass.my_method')
            fq_parts = fq.split('.')
            module_file_name = os.path.splitext(os.path.basename(file_path))[0]
            if module_file_name == "__init__":
                module_file_name = os.path.basename(os.path.dirname(file_path))

            func_path_relative_to_module = fq_parts[-1] # Default: just the last part (for top-level functions)
            
            # Attempt to find the module name's index in the FQDN parts to correctly derive `func_path`.
            # Iterate from the end to find the *last* occurrence of the module name,
            # which is typically the one preceding the function/method path.
            module_name_idx = -1
            for i in range(len(fq_parts) - 1, -1, -1):
                if fq_parts[i] == module_file_name:
                    module_name_idx = i
                    break
            
            if module_name_idx != -1 and module_name_idx + 1 < len(fq_parts):
                # If the module name was found and there are parts after it,
                # these parts constitute the function/method path.
                func_path_relative_to_module = ".".join(fq_parts[module_name_idx + 1:])
            elif module_name_idx == len(fq_parts) - 1:
                # If the module name is the last part of the FQDN (e.g., `mymodule`),
                # this means the FQDN itself is just the module name.
                # Fallback to just the last part as `func_path`.
                func_path_relative_to_module = fq_parts[-1]
            else:
                # If module name not found in FQDN parts or unexpected structure.
                # Fallback to the last part of the FQDN.
                print(f"⚠️ Could not precisely determine function path within module for {fq}. Defaulting to last FQDN component: '{fq_parts[-1]}'")
                func_path_relative_to_module = fq_parts[-1]


            with open(file_path, "r", encoding="utf-8") as f:
                full_source = f.read()

            func_source = None
            try:
                func_source = extract_function_source(full_source, func_path_relative_to_module)
                if not func_source:
                    print(f"⚠️ No source extracted for {fq}, possibly malformed or not found; skipping triviality check.")
                    continue
            except ValueError as e:
                print(f"❌ Error extracting function source for {fq} using path '{func_path_relative_to_module}': {e}")
                continue
            except Exception as e:
                print(f"❌ Unexpected error during source extraction for {fq}: {e}")
                continue

            # Now, check if the extracted function source is trivial using the new logic.
            if is_function_body_trivial(func_source):
                trivial_functions_list.append(fq)

        except FileNotFoundError as e:
            print(f"❌ File not found for {fq}: {e}")
            continue
        except Exception as e:
            print(f"❌ An unexpected error occurred while processing {fq}: {e}")
            continue

    return trivial_functions_list

def get_cleaned_function_bodies(fq_function_names: List[str], source_root: str) -> Dict[str, str]:
    """
    Given a list of fully qualified function names, returns a dictionary where keys are the
    fully qualified names and values are the cleaned source code of the function body.
    The cleaned source code includes only the executable statements, with docstrings,
    comments, and the function definition (e.g., `def ...:`) removed.

    Args:
        fq_function_names (List[str]): A list of fully qualified function names.
        source_root (str): The root directory for resolving fully qualified names.

    Returns:
        Dict[str, str]: A dictionary mapping fully qualified function names to their
                        cleaned body source code. Functions that cannot be processed
                        will be omitted from the dictionary.
    """
    cleaned_bodies = {}

    for fq in fq_function_names:
        try:
            file_path = resolve_function_source_path(fq, source_root)

            # Determine the function/method path relative to its module
            fq_parts = fq.split('.')
            module_file_name = os.path.splitext(os.path.basename(file_path))[0]
            if module_file_name == "__init__":
                module_file_name = os.path.basename(os.path.dirname(file_path))

            func_path_relative_to_module = fq_parts[-1]
            module_name_idx = -1
            for i in range(len(fq_parts) - 1, -1, -1):
                if fq_parts[i] == module_file_name:
                    module_name_idx = i
                    break
            
            if module_name_idx != -1 and module_name_idx + 1 < len(fq_parts):
                func_path_relative_to_module = ".".join(fq_parts[module_name_idx + 1:])
            elif module_name_idx == len(fq_parts) - 1:
                func_path_relative_to_module = fq_parts[-1]
            else:
                print(f"⚠️ Could not precisely determine function path within module for {fq}. Defaulting to last FQDN component: '{fq_parts[-1]}'")
                func_path_relative_to_module = fq_parts[-1]

            with open(file_path, "r", encoding="utf-8") as f:
                full_source = f.read()

            func_source_block = None
            try:
                # This extracts the entire function block: decorators, def line, body, docstring.
                func_source_block = extract_function_source(full_source, func_path_relative_to_module)
                if not func_source_block:
                    print(f"⚠️ No source extracted for {fq}, possibly malformed or not found; skipping.")
                    continue
            except ValueError as e:
                print(f"❌ Error extracting function source for {fq} using path '{func_path_relative_to_module}': {e}")
                continue
            except Exception as e:
                print(f"❌ Unexpected error during source extraction for {fq}: {e}")
                continue

            # Strip comments and docstrings from the function block
            stripped_func_source_block = strip_comments_and_docstrings(func_source_block)

            # Now, parse the stripped function block to get only the function's body statements.
            try:
                # Parse the stripped function block (which should now contain just def line + body)
                tree = ast.parse(stripped_func_source_block)
                
                # The AST should contain one top-level FunctionDef or AsyncFunctionDef node.
                function_node = None
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        function_node = node
                        break

                if not function_node or not function_node.body:
                    # If no function node found, or body is empty (e.g., `def foo(): pass`)
                    # In such cases, the body is effectively empty.
                    cleaned_bodies[fq] = ""
                    continue

                # Get the lines of the stripped function block source
                stripped_lines = stripped_func_source_block.splitlines()

                # The body starts at the `lineno` of the first statement and ends at the `end_lineno` of the last statement.
                # Adjust to 0-based indices for list slicing.
                first_stmt = function_node.body[0]
                last_stmt = function_node.body[-1]

                body_start_line_idx = first_stmt.lineno - 1
                body_end_line_idx = last_stmt.end_lineno - 1

                # Slice the lines to get only the body content
                body_lines_raw = stripped_lines[body_start_line_idx : body_end_line_idx + 1]

                # Determine the minimum indentation level of the function body.
                # This is the col_offset of the first statement.
                min_indent = first_stmt.col_offset

                # Remove the common minimum indentation from each line of the body.
                cleaned_body_lines = []
                for line in body_lines_raw:
                    if line.strip(): # Only process non-empty lines
                        # Ensure line is long enough to have this indentation
                        if len(line) >= min_indent:
                            cleaned_body_lines.append(line[min_indent:])
                        else:
                            # For lines shorter than min_indent (e.g., entirely whitespace lines),
                            # just strip their leading/trailing whitespace.
                            cleaned_body_lines.append(line.strip())
                    else:
                        cleaned_body_lines.append(line.strip()) # Preserve empty lines as empty strings

                cleaned_bodies[fq] = '\n'.join(cleaned_body_lines)

            except SyntaxError as e:
                print(f"❌ Syntax error parsing stripped function source for {fq} (likely malformed after stripping): {e}")
                continue
            except Exception as e:
                print(f"❌ Unexpected error processing function body for {fq} for cleaning: {e}")
                continue

        except FileNotFoundError as e:
            print(f"❌ File not found for {fq}: {e}")
            continue
        except Exception as e:
            print(f"❌ An unexpected error occurred while processing {fq}: {e}")
            continue

    return cleaned_bodies

# --- Orchestration Logic ---

def build_servicewise_function_map_dictionaries(source_folder: str) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    """
    Iterates over packages in source_folder and extracts `_function_map` and `_utils_map` from each __init__.py,
    removing entries that are trivial (contain only `pass`, empty returns, etc.).

    Args:
        source_folder (str): Path to top-level folder (e.g., /APIs).

    Returns:
        Tuple[dict, list]:
            - dict: { package_name: {flattened: fully.qualified.name} } with trivial entries removed.
            - list: A list of fully qualified names of functions that were identified as trivial.
    """
    function_maps = {}
    all_trivial_functions = set() # Use a set to store unique trivial functions

    for entry in os.listdir(source_folder):
        entry_path = os.path.join(source_folder, entry)
        init_path = os.path.join(entry_path, "__init__.py")

        if os.path.isdir(entry_path) and os.path.exists(init_path):
            try:
                # Extract both function_map and utils_map
                fmap = extract_function_map_from_init(init_path)
                utils_map = extract_utils_map_from_init(init_path)
                
                # Combine both maps
                combined_map = {**fmap, **utils_map}
                fq_values = list(combined_map.values())

                # Find trivial functions within the current package
                trivial_fq_in_package = set(find_trivial_functions(fq_values, source_folder))
                all_trivial_functions.update(trivial_fq_in_package)

                # Remove trivial functions from the current function map
                cleaned_map = {k: v for k, v in combined_map.items() if v not in trivial_fq_in_package}

                if cleaned_map:
                    function_maps[entry] = cleaned_map
                else:
                    print(f"ℹ️ All functions in package '{entry}' were found to be trivial; skipping this package.")

            except FileNotFoundError as e:
                print(f"⚠️ Failed to access '__init__.py' or related files for package '{entry}': {e}")
            except Exception as e:
                print(f"⚠️ An unexpected error occurred processing package '{entry}' via '{init_path}': {e}")

    return function_maps, list(all_trivial_functions)




#%%
if __name__ == "__main__":
    # Define the folder paths
    source_folder = './APIs' # Folder with the packages
    output_folder = './Mds' # The output folder to hold md outputs

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Retrieve the function maps and trivial functions for each package
    function_maps, trivial_functions = build_servicewise_function_map_dictionaries(source_folder)
    trivial_function_bodies = get_cleaned_function_bodies(trivial_functions, source_folder)
    print("Trivial Function Bodies:")
    pprint(trivial_function_bodies)
    
    # Convert Python files to Markdown using pydoc and insert flat function names into the module-wise dictionary
    module_wise_dict = convert_py_to_md_with_pydoc(source_folder, output_folder)
    print(module_wise_dict.keys())
    print(function_maps.keys())
    for package in function_maps:
        utils_map = extract_utils_map_from_init(os.path.join(source_folder, package, "__init__.py"))
        insert_flat_function_names(module_wise_dict[package], {package: function_maps[package]})
        markdown = render_modules_to_markdown(module_wise_dict[package])
        
        # Generate the output markdown file path
        output_file = os.path.join(output_folder, f"{package}.md")

        # Write the rendered markdown to the output file
        with open(output_file, "w", encoding="utf-8") as md_file:
            markdown = _process_content(markdown, utils_map)
            md_file.write(markdown)

        print(f"Generated documentation for {package}: {output_file}")