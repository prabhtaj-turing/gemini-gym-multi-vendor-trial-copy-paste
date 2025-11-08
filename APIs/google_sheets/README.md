# Google Sheets API Simulation

This package provides a comprehensive simulation of the Google Sheets API functionality, enabling testing and development of spreadsheet-related workflows without requiring actual Google Sheets access.

## Overview

The Google Sheets API simulation includes modules for spreadsheet management, sheet operations, cell manipulation, and data analysis. It provides a realistic environment for testing Google Sheets integration functionality.

## Components

### Spreadsheets Resource
- **Spreadsheet Management**: Create, read, update, delete spreadsheets
- **Spreadsheet Operations**: 
  - Get spreadsheet metadata and content
  - Update spreadsheet properties
  - Manage spreadsheet structure
  - Handle spreadsheet formatting

### Sheets Resource
- **Sheet Management**: Manage individual sheets within spreadsheets
- **Sheet Operations**:
  - Create and delete sheets
  - Get sheet information
  - Update sheet properties
  - Manage sheet data

### Values Resource
- **Cell Management**: Read and write cell values
- **Value Operations**:
  - Get cell values and ranges
  - Update cell values
  - Clear cell contents
  - Batch update operations

### Charts Resource
- **Chart Management**: Create and manage charts
- **Chart Operations**:
  - Create charts from data
  - Update chart properties
  - Delete charts
  - Manage chart types

### Conditional Formatting
- **Format Management**: Apply conditional formatting rules
- **Format Operations**:
  - Create conditional formatting
  - Update formatting rules
  - Delete formatting rules
  - Manage format conditions

## Key Functions

### Spreadsheet Management
- `create_spreadsheet` - Create new spreadsheets
- `get_spreadsheet` - Get spreadsheet content and metadata
- `update_spreadsheet` - Update spreadsheet properties
- `delete_spreadsheet` - Delete spreadsheets
- `list_spreadsheets` - List available spreadsheets

### Sheet Management
- `create_sheet` - Create new sheets
- `get_sheet` - Get sheet information
- `update_sheet` - Update sheet properties
- `delete_sheet` - Delete sheets
- `list_sheets` - List sheets in spreadsheet

### Cell Operations
- `get_values` - Get cell values
- `update_values` - Update cell values
- `clear_values` - Clear cell contents
- `batch_update_values` - Batch update multiple cells

### Chart Management
- `create_chart` - Create charts
- `update_chart` - Update chart properties
- `delete_chart` - Delete charts
- `list_charts` - List charts in sheet

### Formatting
- `create_conditional_format` - Create conditional formatting
- `update_conditional_format` - Update formatting rules
- `delete_conditional_format` - Delete formatting rules

## Usage

The Google Sheets API simulation provides a realistic environment for testing spreadsheet-related workflows. All functions return simulated data that mimics real Google Sheets API responses, allowing developers to test their Sheets integration code without requiring actual Google Sheets access.

## Features

### Spreadsheet Management
- Full CRUD operations for spreadsheets
- Spreadsheet metadata management
- Spreadsheet sharing and permissions
- Version history support

### Sheet Operations
- Multiple sheet support
- Sheet creation and deletion
- Sheet property management
- Sheet data manipulation

### Cell Management
- Individual cell operations
- Range-based operations
- Batch operations for efficiency
- Data type handling

### Data Analysis
- Formula support
- Chart creation and management
- Conditional formatting
- Data validation

### Integration Features
- Real-time collaboration support
- Data import and export
- Template management
- Comment and suggestion handling

## Error Handling

The module includes comprehensive error simulation that can be configured to test various error scenarios, including authentication errors, permission denied errors, and service-specific errors.

## Testing

The module includes a comprehensive test suite in the `tests/` directory that validates the functionality of all Google Sheets service simulations.

## Dependencies

- `common_utils` - Shared utilities for error handling and simulation
- `SimulationEngine` - Database and state management for simulations

## Data Types Supported

The simulation supports various data types:
- **Text**: Strings and text content
- **Numbers**: Integers, decimals, percentages
- **Dates**: Date and time values
- **Formulas**: Mathematical and logical formulas
- **Boolean**: True/false values
- **Arrays**: Multi-dimensional data

## Chart Types

The simulation supports various chart types:
- **Column Charts**: Vertical bar charts
- **Line Charts**: Line graphs
- **Pie Charts**: Circular charts
- **Scatter Charts**: X-Y scatter plots
- **Area Charts**: Filled area charts
- **Bar Charts**: Horizontal bar charts

## Formula Support

The simulation includes support for common spreadsheet formulas:
- **Mathematical**: SUM, AVERAGE, COUNT, etc.
- **Logical**: IF, AND, OR, etc.
- **Text**: CONCATENATE, LEFT, RIGHT, etc.
- **Date/Time**: NOW, TODAY, DATE, etc.
- **Lookup**: VLOOKUP, HLOOKUP, etc. 