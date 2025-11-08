# Google Agents API Generator

This project implements a series of simulated APIs designed to facilitate the training and testing of Gemini's agentic capabilities. The simulated APIs provide a controlled environment for implementing various use cases and training Gemini to execute actions autonomously.

## Project Overview

The project serves as a sandbox environment where:
- Multiple simulated APIs are implemented to mimic real-world services
- Gemini can be trained to interact with these APIs in an agentic manner
- Various use cases can be tested and validated
- API responses and behaviors can be controlled and monitored

## Prerequisites

- Python 3.11
- Conda package manager
- Git

## Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd google-agents-api-gen
```

2. Create a new conda environment with Python 3.11:
```bash
conda create -n google-agents-api-gen python=3.11
conda activate google-agents-api-gen
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

The project is organized as follows:

```
google-agents-api-gen/
├── APIs/                  # Directory containing all simulated API implementations
│   ├── confluence/        # Confluence API simulation
│   ├── gmail/             # Gmail API simulation
│   ├── google_calendar/   # Google Calendar API simulation
│   ├── google_chat/       # Google Chat API simulation
│   ├── google_docs/       # Google Docs API simulation
│   ├── google_maps/       # Google Maps API simulation
│   ├── google_meet/       # Google Meet API simulation
│   ├── google_sheets/     # Google Sheets API simulation
│   ├── jira/              # Jira API simulation
│   ├── slack/             # Slack API simulation
│   └── ...                # Other API simulations
│
│
├── DBs/                  # Default database files for API simulations
├── HumanDataDBs/         # Human-generated data databases for training
├── notebooks/            # Jupyter notebooks for analysis and development
├── Scripts/              # Utility scripts for API generation and documentation
├── Utils/                # Core utility modules and helper functions
│
├── .github/              # GitHub configuration files
├── .vscode/              # VS Code configuration
├── .coveragerc           # Coverage reporting configuration
│
├── requirements.txt      # Project dependencies
├── pytest.ini            # Pytest configuration
├── README.md             # Project documentation
└── CHANGELOG.md          # Release notes file
```

### Key Components

1. **APIs Directory**: Contains the implementation of each simulated API, organized in separate subdirectories. Each API implementation includes:
   - Endpoint definitions
   - Request/response handling
   - Business logic simulation
   - Data persistence
   - SimulationEngine/ subdirectory for mock implementations
   - tests/ subdirectory for API-specific tests

2. **DBs Directory**: Contains JSON database files that provide default data for each API simulation, including:
   - User data and authentication tokens
   - Sample content and resources
   - Configuration settings
   - Mock responses for testing

3. **Data Directory**: Contains test datasets and sample data for API testing and validation, organized by API type.

4. **Scripts Directory**: Contains utility scripts for:
   - `FCSpec.py`: Function calling specifications for API interactions
   - `AutoDoc.py`: Automatic API documentation generation

5. **Utils Directory**: Contains core utility modules including:
   - `FCSpec.py`: Enhanced function calling specifications
   - `AutoDoc.py`: Advanced documentation generation
   - `HumanReadableDoc.py`: Human-readable documentation creation
   - `RunTests.py`: Test execution utilities
   - `package_to_drive.py`: Packaging utilities for Google Drive integration

6. **Notebooks Directory**: Contains Jupyter notebooks for:
   - Data analysis and exploration
   - Development and testing workflows
   - Error analysis and debugging
   - Multi-hop support implementation

7. **Testing and Coverage**:
   - `tests_coverage/`: Contains test coverage reports
   - `pytest.ini`: Configuration for pytest
   - `.coveragerc`: Coverage reporting configuration

## Development

To contribute to this project:
1. Create a new branch for your feature
2. Implement your changes
3. Add tests for new functionality
4. Submit a pull request

## Testing

The project includes pre-configured test settings for both VS Code and Cursor IDEs. The test configuration is set up in the `.vscode` directory and includes:

1. **Test Discovery**: Tests are automatically discovered in the `APIs` directory
2. **Test Patterns**: Tests are identified by the following patterns:
   - `test_*.py`
   - `*_test.py`
   - `*test*.py`
3. **Python Path**: The workspace and APIs directories are added to the Python path for proper module resolution

### Running Tests

You can run tests in several ways:

1. **Command Line**:
```bash
pytest
```

2. **VS Code/Cursor**:
   - Use the Testing sidebar (flask icon)
   - Tests will be automatically discovered
   - Run individual tests or entire test suites
   - View test results and coverage directly in the IDE

The test configuration is already set up in the `.vscode/settings.json` file, so no additional configuration is needed when opening the project in VS Code or Cursor.

## Code Coverage

You can view the latest code coverage report here: [Coverage Report](https://sturdy-doodle-6v94em3.pages.github.io/index.html)
