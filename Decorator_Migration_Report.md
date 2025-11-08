# Transition to Decorator-Based Tool Specifications

## 1. Goal

The primary goal of this initiative is to modernize and stabilize our Function Calling (FC) Spec generation pipeline. We aim to:

*   **Decouple FC Spec generation from Python docstrings**, removing the need for complex and error-prone translation logic.
*   **Codify the FC Spec as a decorator**, making it a direct, definitive, and machine-readable part of the tool's implementation.
*   **Automate the detection of required parameters** by inferring them directly from the function's signature.(only for the function level params)
*   **Establish a foundation for future enhancements**, such as using Pydantic models for even greater flexibility and validation.

## 2. The Change: What Was Implemented

We have developed and executed an automated script, `decorator_injector.py`, that migrates our existing, generated JSON schemas into `@tool_spec` decorators. These decorators have been injected directly above their corresponding tool functions across the entire codebase.

This change makes the FC Spec a first-class citizen in our code, co-located with the function it describes.

## 3. Impact and Benefits

The impact of this change is a significant improvement in the reliability and maintainability of our tool definitions.

*   **Simplified Schema Generation:** The new FC Spec generation script (`Scripts/new_fcspec.py`) now introspects the code directly. It simply imports a tool function and accesses its `.spec` attribute to retrieve the schema. This eliminates the previous, complex translation layer.
*   **Increased Reliability:** By removing the docstring-to-schema translation step, we have eliminated a major source of potential errors. The decorator is now the single source of truth, ensuring that the code and its specification are tightly coupled.
*   **Seamless Integration:** The new generation script maintains the same interface as the old one, allowing for a drop-in replacement in our existing workflows.

## 4. Downsides and Next Steps

While this is a major step forward, there are important next steps to consider:

*   **Hybrid Approach:** The codebase now contains both docstrings and decorators. The long-term goal is to refactor the tools to rely solely on the decorator for schema information, allowing docstrings to focus purely on human-readable documentation.
*   **Update Documentation Workflows:** The script that generates human-readable documentation must be updated to read from the new `@tool_spec` decorators instead of parsing docstrings.
*   **Inherited Imperfections:** This automated migration is on par with the previous system, which means any flaws or inaccuracies in the original JSON schemas have been carried over into the decorators. Some decorators will require manual review to fully integrate information that was previously only in the docstring or to fix these inherited issues.

## 6. Implementation Overview

The automated injection was performed by the `DevScripts/decorator_injector.py` script. The process is as follows:

1.  **Discover Tools**: The script first extracts all `_function_map` dictionaries from the `APIs/` directory to build a comprehensive list of every tool in the system.
2.  **Load Schemas**: It loads all existing JSON schemas from the `Schemas/` directory into memory.
3.  **Locate Functions**: For each tool, it uses an enhanced `locate_tool_function` utility to parse the relevant Python file's Abstract Syntax Tree (AST). This allows it to pinpoint the exact starting line number of each function definition and determine if a `@tool_spec` decorator already exists.
4.  **Generate & Inject**: This is the core of the operation. For each function that needs a decorator:
    *   **Code Generation**: The corresponding JSON schema is passed to the `format_fcspec_to_decorator` function, which returns a complete, multi-line `@tool_spec(...)` decorator as a Python string.
    *   **File-by-File Processing**: The script groups all required injections by their target file. It then iterates through each file, reads its entire content into a list of lines, and prepares to insert the new code.
    *   **Reverse Order Injection**: Crucially, all decorator injections for a single file are sorted by line number in **reverse order**. This is a critical step to ensure that inserting new lines of code does not shift the line numbers and invalidate the locations for subsequent injections in the same file.
    *   **Import Handling**: After all decorators for a file are inserted, the script checks if the necessary `from common_utils.decorators import tool_spec` import exists. If not, it intelligently inserts it at the top of the file, correctly placing it after any docstrings or `from __future__`(There is an issue with this) imports to maintain valid Python syntax.
    *   **Final Write**: The modified list of lines is written back to the file, finalizing the injection.

## 7. Path to Production

This work has been developed on the `fcspec_decorator_injection` feature branch. The following steps will be taken to merge this change into the main development branch:

1.  **Finalize Injection**: The `decorator_injector.py` script has been run on the feature branch, applying the decorators to all target files.
2.  **Replace Schema Generation Logic**: The project's primary schema generation workflow will be updated to use the new `Scripts/new_fcspec.py` script, which generates schemas from the decorators. The old docstring-based generation script will be deprecated.
3.  **Cleanup**: All temporary and development scripts (`decorator_injector.py`, `isolated_test.py`, etc.) and log files created during this process will be removed from the branch.
4.  **Merge**: The cleaned `fcspec_decorator_injection` branch will be merged into the `development` branch, officially launching this change.

