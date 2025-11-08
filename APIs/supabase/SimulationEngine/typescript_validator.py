from common_utils.print_log import print_log
import requests
import quickjs
import json
from typing import Tuple, List, Dict, Any

# URL for the standalone browser version of the TypeScript compiler
TYPESCRIPT_COMPILER_URL = "https://cdn.jsdelivr.net/npm/typescript@5.4.5/lib/typescript.js"

class PurePythonTypeScriptValidator:
    """
    Validates TypeScript code strings using an embedded JavaScript engine,
    without needing Node.js or npm installed on the system.
    """
    def __init__(self, ts_compiler_js_code: str):
        """
        Initializes the validator by loading the typescript.js compiler
        into a new JavaScript context.
        """
        print_log("Initializing JavaScript engine and loading TypeScript compiler...")
        self.context = quickjs.Context()
        # Load the massive typescript.js file into the JS engine.
        # This makes the global `ts` object available.
        self.context.eval(ts_compiler_js_code)
        print_log("Compiler loaded successfully.")

    def validate(self, ts_code: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validates the given TypeScript code string.

        Returns a tuple: (is_valid, diagnostics_list)
        """
        js_validation_script = f"""
        (function() {{
            const code = {json.dumps(ts_code)};
            let diagnostics = [];
            let fatalError = null;
            // Compiler options for strict validation.
            const options = {{
                compilerOptions: {{
                    target: ts.ScriptTarget.ES2020,
                    module: ts.ModuleKind.ESNext,
                    strict: true,
                    noEmit: true,
                    skipLibCheck: true,
                    skipDefaultLibCheck: true
                }}
            }};
            try {{
                // Try to create a source file (catches fatal parse errors)
                ts.createSourceFile("temp.ts", code, ts.ScriptTarget.ES2020, true);
            }} catch (e) {{
                fatalError = e && e.message ? e.message : String(e);
            }}
            // Use transpileModule for single-file validation
            const result = ts.transpileModule(code, options);
            diagnostics = result.diagnostics || [];
            // Convert diagnostics to a simple array of objects
            const simpleDiagnostics = diagnostics.map(d => {{
                return {{
                    messageText: d.messageText,
                    category: d.category,
                    code: d.code
                }};
            }});
            if (fatalError) {{
                simpleDiagnostics.push({{ messageText: fatalError, category: 1, code: -1 }});
            }}
            // Return as JSON string
            return JSON.stringify(simpleDiagnostics);
        }})();
        """
        try:
            diagnostics_json = self.context.eval(js_validation_script)
            diagnostics = json.loads(diagnostics_json)
            # Treat as invalid if any diagnostic is an error (category === 1)
            is_valid = not any(d.get('category', 0) == 1 for d in diagnostics)
            # Debug log for diagnostics
            print_log("Diagnostics:", json.dumps(diagnostics, indent=2))
            return is_valid, diagnostics
        except quickjs.JSException as e:
            return False, [{'messageText': f'A fatal syntax error occurred: {e}', 'category': 1, 'code': -1}]


def format_diagnostics(diagnostics: List[Dict[str, Any]]) -> str:
    """Formats the diagnostic messages from TypeScript into a readable string."""
    if not diagnostics:
        return "No errors found."
    
    formatted_errors = []
    for diag in diagnostics:
        # messageText can be a string or a nested dictionary for complex errors
        message = diag.get('messageText')
        if isinstance(message, dict):
            message = message.get('messageText', 'Complex error message.')
        formatted_errors.append(message)
        
    return "; ".join(formatted_errors)

_validator_cache = None

# Initialize the validator with the downloaded compiler code
def get_validator():
    """Downloads the TypeScript compiler and returns a validator instance."""
    global _validator_cache
    if _validator_cache is None:
        try:
            response = requests.get(TYPESCRIPT_COMPILER_URL)
            response.raise_for_status()  # Raise an exception for bad status codes
            ts_compiler_source = response.text
            _validator_cache = PurePythonTypeScriptValidator(ts_compiler_source)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to download TypeScript compiler: {e}") 
    return _validator_cache