# SDK JSON Persistence Analyzer

This is an enhanced version of the JSON serialization checker specifically designed for SDK data persistence analysis. It ensures that all SDK methods return data that can be safely saved to JSON files. The tool uses intelligent LLM analysis to provide more accurate and comprehensive results, following the pattern used in the `apis_comparison` script with incremental CSV saving, resume capability, and parallel processing.

## 🚀 Key Improvements

### 1. **LLM-Powered Analysis**
- Uses Google's Gemini model for intelligent analysis of SDK serialization issues
- Provides detailed explanations and recommendations for each SDK method
- Reduces false positives through contextual understanding of data persistence needs

### 2. **Incremental CSV Saving**
- Results are saved continuously as they're processed
- No data loss if the process is interrupted
- Real-time progress tracking

### 3. **Resume Capability**
- Can resume from where it left off if interrupted
- Identifies incomplete entries automatically
- Only processes functions that need re-analysis

### 4. **Enhanced Error Detection**
- Better detection of non-serializable objects that would break JSON file saving
- Categorizes issues by type (custom objects, generators, callables, file handles, etc.)
- More detailed error analysis for SDK data persistence scenarios

### 5. **Parallel Processing**
- Multi-threaded processing for faster analysis
- Configurable thread count
- Thread-safe CSV writing

### 6. **Comprehensive Reporting**
- Detailed CSV output with all analysis dimensions
- Markdown summary report with statistics
- SDK module breakdown and issue categorization

## 📋 Prerequisites

1. **Python 3.7+**
2. **Google Gemini API Key** - Get one from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **Required packages** (install via `pip install -r requirements.txt`):
   - `google-generativeai`
   - `python-dotenv`

## 🛠️ Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp env.template .env
   # Edit .env and add your Gemini API key
   ```

3. **Verify setup**:
   ```bash
   python run_improved_json_check.py
   # Select option 1 to check prerequisites
   ```

## 🎯 Usage

### Interactive Mode
```bash
python run_improved_json_check.py
```

**Menu Options**:
1. **Check prerequisites** - Verify all requirements are met
2. **Show configuration** - Display current settings
3. **List available SDK modules** - Show all SDK modules that will be analyzed
4. **Run SDK JSON persistence analysis** - Start full analysis
5. **Analyze existing results** - View statistics from previous runs
6. **Resume incomplete analysis** - Continue from where you left off
7. **Analyze incomplete entries** - Identify SDK methods needing re-analysis
8. **Exit** - Quit the program

### Direct Execution
```bash
# Run full analysis
python improved_json_serialization_checker.py

# Or import and use programmatically
from improved_json_serialization_checker import run_improved_json_serialization_check
run_improved_json_serialization_check()
```

## 📊 Output Files

### CSV Output (`improved_json_serialization_check.csv`)
Contains detailed results for each SDK method with columns:
- `api_name` - Name of the SDK module
- `function_name` - Name of the SDK method
- `file_path` - Path to the function file
- `function_signature` - Function signature
- `is_json_serializable` - Boolean indicating serialization status
- `has_custom_objects` - Contains custom Python objects
- `has_generators` - Contains generator objects
- `has_callables` - Contains callable objects
- `has_file_handles` - Contains file handles
- `has_network_objects` - Contains network objects
- `has_threading_objects` - Contains threading objects
- `requires_parameters` - Function requires parameters
- `execution_successful` - Function executed successfully
- `execution_status` - Status of execution attempt
- `error_details` - Detailed error information
- `return_type_analysis` - Analysis of return type
- `serialization_notes` - Notes about serialization
- `analysis_notes` - LLM analysis notes
- `recommendations` - LLM recommendations
- `timestamp` - Analysis timestamp

### Summary Report (`improved_json_serialization_summary.md`)
Comprehensive markdown report including:
- Summary statistics
- Execution status breakdown
- Issue type breakdown
- SDK module breakdown table
- SDK modules requiring attention
- Sample SDK methods breaking JSON persistence

## ⚙️ Configuration

### Environment Variables (`.env` file)
```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional (with defaults)
GEMINI_MODEL_NAME=gemini-2.5-flash-preview-05-20
MAX_THREADS=6
TIMEOUT_SECONDS=30
API_CALL_DELAY=6
```

### Processing Configuration
- **MAX_THREADS**: Number of parallel threads (default: 6)
- **TIMEOUT_SECONDS**: Timeout per API processing (default: 30)
- **API_CALL_DELAY**: Delay between LLM API calls (default: 6)

## 🔍 Analysis Dimensions

The improved checker analyzes SDK methods across multiple dimensions:

1. **JSON Serialization**: Basic serialization check for file persistence
2. **Custom Objects**: Detection of custom Python objects that can't be saved to JSON
3. **Generators**: Detection of generator objects that need conversion to lists
4. **Callables**: Detection of callable objects that can't be serialized
5. **File Handles**: Detection of file-like objects that would break JSON saving
6. **Network Objects**: Detection of network-related objects (sockets, connections)
7. **Threading Objects**: Detection of threading objects (locks, threads)
8. **Parameter Requirements**: SDK methods requiring parameters
9. **Execution Success**: Whether SDK method executed successfully

## 🚨 Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not configured"**
   - Ensure you have a valid API key in your `.env` file
   - Get a key from [Google AI Studio](https://makersuite.google.com/app/apikey)

2. **"Import error"**
   - Install required packages: `pip install -r requirements.txt`
   - Check Python version (requires 3.7+)

3. **"SDK modules directory not found"**
   - Ensure you're running from the correct directory
   - Check that `../../APIs` exists relative to the script

4. **"API call failed"**
   - Check your internet connection
   - Verify your API key is valid
   - Check API rate limits

### Performance Tips

1. **Adjust thread count** based on your system capabilities
2. **Increase timeout** for large APIs
3. **Use resume mode** if the process is interrupted
4. **Monitor API usage** to avoid rate limits

## 📈 Comparison with Original

| Feature | Original | Improved |
|---------|----------|----------|
| Analysis Method | Static + Basic dynamic | Static + Dynamic + LLM |
| CSV Saving | Batch at end | Incremental |
| Resume Capability | No | Yes |
| Error Detection | Basic | Comprehensive |
| Issue Categorization | Limited | Detailed |
| Recommendations | None | LLM-generated |
| Parallel Processing | Basic | Enhanced |
| Progress Tracking | Limited | Real-time |
| SDK Focus | Generic | JSON persistence specific |

## 🤝 Contributing

To contribute to the improved checker:

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Test with multiple APIs

## 📄 License

This project follows the same license as the parent repository. 