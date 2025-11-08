# Copilot API Simulation

This package provides a comprehensive simulation of the Copilot API functionality, enabling testing and development of AI-powered coding assistant workflows without requiring actual Copilot access.

## Overview

The Copilot API simulation includes modules for code intelligence, file system operations, command line operations, VS Code environment management, project setup, code quality, version control, and test file management. It provides a realistic environment for testing Copilot-related functionality.

## Components

### Code Intelligence
- **Semantic Search**: Search code semantically for relevant functions and classes
- **Code Usage Analysis**: List usages of specific code elements
- **Grep Search**: Perform text-based searches in codebase

### File System Operations
- **File Search**: Search for files in the workspace
- **File Reading**: Read file contents
- **Directory Listing**: List directory contents
- **File Editing**: Insert and edit content in files

### Command Line Operations
- **Terminal Execution**: Run commands in terminal
- **Output Retrieval**: Get terminal command outputs

### VS Code Environment
- **API Access**: Get VS Code API functionality
- **Extension Management**: Install and manage VS Code extensions

### Project Setup
- **Workspace Creation**: Create new development workspaces
- **Project Information**: Get project setup details
- **Notebook Creation**: Create new Jupyter notebooks

### Code Quality & Version Control
- **Error Detection**: Get code errors and issues
- **Change Tracking**: Get information about changed files

### Test File Management
- **Test Search**: Search for test files and test-related content

## Key Functions

### Code Intelligence
- `semantic_search` - Search code semantically
- `list_code_usages` - List usages of code elements
- `grep_search` - Perform text-based code search

### File System
- `file_search` - Search for files
- `read_file` - Read file contents
- `list_dir` - List directory contents
- `insert_edit_into_file` - Insert edits into files

### Command Line
- `run_in_terminal` - Execute terminal commands
- `get_terminal_output` - Get terminal command output

### VS Code Environment
- `get_vscode_api` - Access VS Code API
- `install_extension` - Install VS Code extensions

### Project Setup
- `create_new_workspace` - Create new workspace
- `get_project_setup_info` - Get project information
- `create_new_jupyter_notebook` - Create Jupyter notebook

### Code Quality & Version Control
- `get_errors` - Get code errors
- `get_changed_files` - Get changed files

### Test File Management
- `test_search` - Search for test files

## Usage

The Copilot API simulation provides a realistic environment for testing AI-powered coding assistant workflows. All functions return simulated data that mimics real Copilot API responses, allowing developers to test their Copilot integration code without requiring actual Copilot access.

## Features

### Code Intelligence
- Semantic understanding of code structure
- Intelligent code search and analysis
- Usage tracking and dependency analysis

### Development Environment
- VS Code integration simulation
- Extension management
- Project workspace management

### Code Quality
- Error detection and reporting
- Version control integration
- Code quality metrics

### File Management
- Intelligent file operations
- Content editing and manipulation
- Directory structure management

## Error Handling

The module includes comprehensive error simulation that can be configured to test various error scenarios, including file system errors, network failures, and API-specific errors.

## Testing

The module includes a comprehensive test suite in the `tests/` directory that validates the functionality of all Copilot service simulations.

## Dependencies

- `common_utils` - Shared utilities for error handling and simulation
- `SimulationEngine` - Database and state management for simulations

## Schema

The module includes a `schema.json` file that defines the structure and validation rules for the Copilot API simulation. 