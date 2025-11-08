# Google Search API Simulation

This package provides a comprehensive simulation of the Google Search API functionality, enabling testing and development of search-related workflows without requiring actual Google Search access.

## Overview

The Google Search API simulation includes modules for web search, search operations, and search result handling. It provides a realistic environment for testing Google Search integration functionality.

## Components

### Search Resource
- **Search Management**: Perform web searches and retrieve results
- **Search Operations**: 
  - Execute web searches
  - Get search results and metadata
  - Handle search queries and parameters
  - Manage search result pagination
  - Handle search filters and options

### Search Result Management
- **Result Management**: Handle search results and data
- **Result Operations**:
  - Process search result data
  - Handle result metadata
  - Manage result formatting
  - Handle result filtering

## Key Functions

### Search Operations
- `perform_search` - Execute web searches
- `get_search_results` - Get search results
- `search_with_filters` - Search with specific filters
- `search_images` - Search for images
- `search_videos` - Search for videos
- `search_news` - Search for news articles
- `search_shopping` - Search for shopping results

### Search Result Management
- `get_result_details` - Get detailed result information
- `list_search_results` - List search results
- `filter_results` - Filter search results
- `sort_results` - Sort search results
- `get_result_metadata` - Get result metadata

### Advanced Search Features
- `search_by_location` - Location-based search
- `search_by_date` - Date-filtered search
- `search_by_language` - Language-specific search
- `search_by_site` - Site-specific search
- `search_by_file_type` - File type search

## Usage

The Google Search API simulation provides a realistic environment for testing search-related workflows. All functions return simulated data that mimics real Google Search API responses, allowing developers to test their search integration code without requiring actual Google Search access.

## Features

### Search Features
- Web search functionality
- Image search capabilities
- Video search support
- News search features
- Shopping search integration
- Advanced search filters

### Search Result Features
- Comprehensive result data
- Result metadata handling
- Result pagination support
- Result filtering capabilities
- Result sorting options

### Search Options
- Location-based search
- Date range filtering
- Language-specific search
- Site-specific search
- File type filtering
- Safe search options

### Integration Features
- Real-time search results
- Search result caching
- Search analytics and reporting
- Search result export
- Search history tracking

## Error Handling

The module includes comprehensive error simulation that can be configured to test various error scenarios, including network failures, rate limiting, invalid queries, and service-specific errors.

## Testing

The module includes a comprehensive test suite in the `tests/` directory that validates the functionality of all Google Search service simulations.

## Dependencies

- `common_utils` - Shared utilities for error handling and simulation
- `SimulationEngine` - Database and state management for simulations

## Search Types Supported

The simulation supports various search types:
- **Web Search**: General web search results
- **Image Search**: Image search results
- **Video Search**: Video search results
- **News Search**: News article search
- **Shopping Search**: Product search results
- **Book Search**: Book search results
- **Patent Search**: Patent search results

## Search Result Types

The simulation handles various result types:
- **Web Pages**: HTML page results
- **Images**: Image file results
- **Videos**: Video file results
- **News Articles**: News content results
- **Products**: Shopping product results
- **Books**: Book information results
- **Patents**: Patent document results

## Search Filters

The simulation supports various search filters:
- **Date Filters**: Time-based filtering
- **Location Filters**: Geographic filtering
- **Language Filters**: Language-specific results
- **Site Filters**: Domain-specific search
- **File Type Filters**: File format filtering
- **Safe Search**: Content filtering options
- **Custom Filters**: User-defined filters 