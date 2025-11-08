# API Version Comparison Tool

This tool compares API functions between version 0.0.1 and 0.0.8 across multiple dimensions and generates detailed reports.

## Features

- **Function-by-function comparison** between two API versions
- **Parallel processing** for faster analysis using multiple threads
- **AI-powered analysis** using Google's Gemini API
- **Multiple output formats**: CSV for data analysis and Markdown for human-readable changelog
- **Comprehensive dimension analysis** including:
  - New functions detection
  - Input validation changes
  - Function signature changes
  - Implementation logic changes
  - And more...

## Prerequisites

1. **Python 3.7+** installed
2. **Google Generative AI library**: `pip install google-generativeai`
3. **Python-dotenv library**: `pip install python-dotenv`
4. **Gemini API key**: Get one from [Google AI Studio](https://makersuite.google.com/app/apikey)
5. **Version directories**: Both `APIs_V0.0.1` and `APIs_V0.0.8` directories must exist in the same directory as the script

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   # Copy the template file
   cp env.template .env
   
   # Edit .env file with your API key
   nano .env  # or use your preferred editor
   ```

3. **Configure your .env file:**
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   GEMINI_MODEL_NAME=gemini-2.5-flash-preview-05-20
   API_CALL_DELAY=6
   MAX_FUNCTION_THREADS=10
   MAX_ANALYSIS_THREADS=10
   ```

4. **Ensure directory structure:**
   ```
   your_project/
   ├── APIs_V0.0.1/          # Version 0.0.1 APIs
   ├── APIs_V0.0.8/          # Version 0.0.8 APIs
   ├── api_version_comparison.py
   ├── run_comparison.py
   ├── requirements.txt
   ├── env.template
   ├── .env                  # Your configuration (don't commit this!)
   └── README.md
   ```

5. **Run the comparison:**
   ```bash
   python run_comparison.py
   ```

## Configuration

All configuration is now managed through the `.env` file for security:

```bash
# Gemini API Configuration
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL_NAME=gemini-2.5-flash-preview-05-20

# Rate limiting (seconds between API calls)
API_CALL_DELAY=6

# Threading (adjust based on your system)
MAX_FUNCTION_THREADS=10
MAX_ANALYSIS_THREADS=10
```

**Important**: Never commit the `.env` file to version control! It contains your API key.

For specific API targeting, you can still modify the `TARGET_APIS` list in `api_version_comparison.py`:

```python
# Target APIs (leave empty for all)
TARGET_APIS = [
    # "cursor",
    # "jira",
    # etc.
]
```

## Analysis Dimensions

The tool analyzes the following dimensions for each function:

1. **new_function** (bool): Whether the function is new in v0.0.8
2. **function_input_validation_implementation** (bool): Changes in input validation
3. **function_inputs_changes** (bool): Changes to input parameters
4. **function_input_signature_change** (bool): Changes to function signature
5. **function_output_signature_change** (bool): Changes to return type/structure
6. **function_implementation_logic_change** (bool): Changes to core logic
7. **other_changes** (bool): Other significant changes

## Output Files

The tool generates two main outputs in the `comparison_results/` directory:

### 1. CSV Report (`api_version_comparison.csv`)
- Machine-readable format for data analysis
- Contains all analyzed functions with boolean flags for each dimension
- Includes detailed analysis notes for each function

### 2. Markdown Changelog (`api_version_changelog.md`)
- Human-readable format for documentation
- Organized by API and change type
- Summary statistics and detailed change descriptions

## Usage Examples

### Basic Usage
```bash
python run_comparison.py
```

### Direct Script Usage
```bash
python api_version_comparison.py
```

### Compare Specific APIs
Edit the `TARGET_APIS` list in `api_version_comparison.py`:
```python
TARGET_APIS = ["cursor", "jira", "gmail"]
```

## Menu Options

The interactive runner provides these options:

1. **Check prerequisites** - Verify all requirements are met
2. **Show configuration** - Display current settings
3. **List available APIs** - Show APIs in both versions
4. **Run comparison** - Execute the full comparison
5. **Exit** - Close the tool

## Performance

- **Parallel processing**: Uses multiple threads to analyze functions simultaneously
- **Rate limiting**: Respects Gemini API rate limits
- **Efficient parsing**: Uses AST parsing for accurate function extraction
- **Progress tracking**: Shows real-time progress during analysis

## Typical Analysis Time

- **Small API** (10-20 functions): 2-5 minutes
- **Medium API** (50-100 functions): 10-20 minutes
- **Large API** (200+ functions): 30-60 minutes

*Times depend on API complexity, network speed, and Gemini API response times.*

## Error Handling

The tool includes comprehensive error handling:

- **Connection errors**: Automatic retry with exponential backoff
- **API rate limits**: Intelligent rate limiting and queuing
- **File parsing errors**: Graceful handling of malformed files
- **Thread safety**: Protected shared resources

## Output Structure

### CSV Columns
- `api_name`: Name of the API
- `function_name`: Name of the function
- `file_path`: Relative path to the file
- `new_function`: Boolean indicating if function is new
- `function_input_validation_implementation`: Boolean for validation changes
- `function_inputs_changes`: Boolean for input parameter changes
- `function_input_signature_change`: Boolean for signature changes
- `function_output_signature_change`: Boolean for output changes
- `function_implementation_logic_change`: Boolean for logic changes
- `other_changes`: Boolean for other changes
- `analysis_notes`: Detailed analysis from Gemini
- `changelog_summary`: Brief summary for changelog

### Markdown Structure
- **Summary**: Overall statistics
- **API Sections**: Grouped by API name
- **Change Categories**: New functions, changed functions
- **Detailed Descriptions**: AI-generated change descriptions

## Troubleshooting

### Common Issues

1. **"google-generativeai not found"**
   - Run: `pip install google-generativeai`

2. **"python-dotenv not found"**
   - Run: `pip install python-dotenv`

3. **"GEMINI_API_KEY not configured"**
   - Create a `.env` file: `cp env.template .env`
   - Edit the `.env` file with your actual API key
   - Ensure the `.env` file is in the same directory as the script

4. **"Version directory not found"**
   - Ensure `APIs_V0.0.1` and `APIs_V0.0.8` directories exist
   - Check directory names are exact matches

5. **"Gemini API Error"**
   - Verify your API key is correct in the `.env` file
   - Make sure the `.env` file exists in the same directory as the script
   - Check your internet connection
   - Ensure you have API quota available

6. **"Function extraction failed"**
   - Check if Python files are valid syntax
   - Ensure files are UTF-8 encoded

### Performance Tuning

1. **Reduce threads** if you encounter rate limits (edit `.env` file):
   ```bash
   MAX_FUNCTION_THREADS=3
   ```

2. **Increase delay** between API calls (edit `.env` file):
   ```bash
   API_CALL_DELAY=10
   ```

3. **Target specific APIs** to reduce analysis time:
   ```python
   TARGET_APIS = ["cursor", "jira"]
   ```

## API Key Setup

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set it in the configuration:
   ```python
   GEMINI_API_KEY = "your-api-key-here"
   ```

## Support

For issues or questions:
1. Check the error messages in the console output
2. Verify your configuration matches the requirements
3. Ensure all prerequisites are met
4. Review the troubleshooting section

## License

This tool is provided as-is for API version comparison purposes. 