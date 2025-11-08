# Tech Debt Analyzer: Developer Guide

This document provides a comprehensive overview of the Tech Debt Analyzer framework, including its architecture, workflow, and instructions for extending it with new analysis criteria.

## 1. How the Analyzer Works

The Tech Debt Analyzer is a modular, configuration-driven tool designed to perform automated code quality and technical debt analysis on API services using a Large Language Model (LLM).

### Core Components

The framework is composed of several key components:

-   **`main.py`**: The main entry point and orchestrator of the analysis process. It handles command-line argument parsing, configuration loading, discovering target functions, and managing the parallel execution of analysis checks.
-   **`analyzer.py`**: The core analysis engine. This module is responsible for all interactions with the Gemini API. It contains functions for each specific analysis check, which format the prompts, send requests to the LLM, and parse the structured response (`CATEGORY` and `NOTES`) using regular expressions.
-   **`utils.py`**: A collection of helper functions for file system operations and code parsing. This includes discovering Python files, extracting `_function_map` dictionaries from service `__init__.py` files, and parsing individual function code from a file.
-   **`config.json`**: The heart of the framework. This central configuration file defines every aspect of the analysis, including which checks are available, whether they are enabled, their target type (function or project), and which prompt file they use.
-   **`prompts/`**: A directory containing all the LLM prompt templates as `.txt` files. Each file is a detailed set of instructions for the LLM for a specific analysis check.
-   **`results/`**: The output directory where the final analysis report, `results.json`, is stored.

### Workflow

The tool executes the following workflow when run:

1.  **Initialization**: `main.py` parses the command-line arguments (`--services` and `--checks`) to determine the scope of the analysis.
2.  **Configuration Loading**: It loads the `config.json` file and configures the Gemini API client using the credentials from the environment variables.
3.  **Function Discovery**: For each service specified, `main.py` uses `utils.extract_function_map` to parse the `__init__.py` file and identify the public-facing functions from the `_function_map`. This creates a precise list of functions to be analyzed.
4.  **Orchestration**: `main.py` iterates through the checks enabled in `config.json` (and specified in the `--checks` argument, if provided).
5.  **Parallel Execution**: Using a `ThreadPoolExecutor`, it assigns analysis tasks to multiple threads for concurrent processing.
6.  **Analysis Execution**: For each function and check combination:
    a. The corresponding prompt template is read from the `prompts/` directory.
    b. The relevant analysis function in `analyzer.py` (e.g., `analyze_docstring_quality`) is called.
    c. The analyzer function formats the prompt with the function's code (or project structure data) and sends the request to the Gemini API via `call_gemini_api_threadsafe`.
    d. The LLM's response is received.
    e. The analyzer function uses its specific set of regular expressions to parse the `CATEGORY` and `NOTES` from the text response.
7.  **Result Aggregation**: The main orchestrator collects the parsed results from all threads.
8.  **Report Generation**: The final, structured results are compiled into a single dictionary and written to `results/results.json`.

---

## 2. How to Integrate a New Analysis Criterion

Adding a new analysis check is a straightforward process that primarily involves creating a new prompt and updating the configuration, with minimal changes to the Python code.

### Step 1: Create the Prompt File

First, create a new prompt template for your analysis.

1.  Create a new `.txt` file in the `tech_debt_analyzer/prompts/` directory. The name should be descriptive, for example: `error_handling_review.txt`.
2.  Write the prompt. This should be a detailed set of instructions for the LLM.
    -   For function-level checks, use the `{code}` placeholder where the function's source code should be injected.
    -   **Crucially**, you must define a clear and consistent `RESPONSE FORMAT` section. This section must instruct the LLM to return a `CATEGORY` and `NOTES`, as the analyzer's parsing logic depends on this structure.

    **Example:**
    ```text
    TASK: Analyze the quality of error handling in the following function.

    Function Code:
    {code}

    RESPONSE FORMAT:
    You must choose ONE of these categories.

    CATEGORY: [Robust|Adequate|Poor|Missing]
    NOTES: [Provide a justification for your rating.]
    ```

### Step 2: Update `config.json`

Next, add an entry for your new check in the `tech_debt_analyzer/config.json` file.

1.  Open `config.json`.
2.  Add a new JSON object to the `checks` array.
3.  Populate the object with the following key-value pairs:
    -   `"name"`: A human-readable name (e.g., "Error Handling Review").
    -   `"enabled"`: Set to `true` to run the check by default.
    -   `"target_type"`: Set to `"function"` or `"project"`.
    -   `"prompt_template_file"`: The path to your new prompt file (e.g., `"prompts/error_handling_review.txt"`).
    -   `"output_key"`: A unique, machine-readable key for the results JSON (e.g., `"error_handling_review"`).

### Step 3: Update `analyzer.py`

Now, create the function that will parse the response for your new check.

1.  Open `tech_debt_analyzer/analyzer.py`.
2.  Create a new analysis function (e.g., `analyze_error_handling`). The easiest way is to copy an existing function like `analyze_docstring_quality` and modify it.
3.  **This is the most important step:** Update the parsing logic inside your new function to match the `RESPONSE FORMAT` you defined in your prompt.
    -   Modify the `category_patterns` list to include the regex patterns that will capture the category from your new check's response.
    -   Modify the `notes_patterns` list to capture the notes.
    -   Update the `valid_categories` list with the exact category names you defined in your prompt.

### Step 4: Update `main.py`

Finally, connect your new check to the main orchestrator.

1.  Open `tech_debt_analyzer/main.py`.
2.  Find the `analysis_functions` dictionary.
3.  Add a new entry that maps your new `output_key` from `config.json` to your new analysis function in `analyzer.py`.

    **Example:**
    ```python
    analysis_functions = {
        "docstring_quality": analyzer.analyze_docstring_quality,
        # ... existing checks
        "error_handling_review": analyzer.analyze_error_handling, # Add your new line here
    }
    ```

### Step 5: Run and Verify

Your new check is now fully integrated. Run it on a single service to test it:

```bash
python3 tech_debt_analyzer/main.py --services mysql --checks error_handling_review
```

Inspect the `results/results.json` file to ensure the output is correctly parsed and formatted.
