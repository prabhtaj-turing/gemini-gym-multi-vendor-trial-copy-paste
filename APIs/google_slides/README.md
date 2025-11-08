# Google Slides API Simulation

This package provides a comprehensive simulation of the Google Slides API functionality, enabling testing and development of presentation-related workflows without requiring actual Google Slides access.

## Overview

The Google Slides API simulation includes modules for presentation management, slide operations, shape manipulation, and content management. It provides a realistic environment for testing Google Slides integration functionality.

## Components

### Presentations Resource
- **Presentation Management**: Create, read, update, delete presentations
- **Presentation Operations**: 
  - Get presentation metadata and content
  - Update presentation properties
  - Manage presentation structure
  - Handle presentation formatting

### Slides Resource
- **Slide Management**: Manage individual slides within presentations
- **Slide Operations**:
  - Create and delete slides
  - Get slide information
  - Update slide properties
  - Manage slide content

### Shapes Resource
- **Shape Management**: Create and manage shapes and text boxes
- **Shape Operations**:
  - Create shapes and text boxes
  - Update shape properties
  - Delete shapes
  - Manage shape formatting

### Images Resource
- **Image Management**: Insert and manage images
- **Image Operations**:
  - Insert images into slides
  - Update image properties
  - Delete images
  - Manage image positioning

### Tables Resource
- **Table Management**: Create and manage tables
- **Table Operations**:
  - Create tables
  - Update table content
  - Delete tables
  - Manage table formatting

## Key Functions

### Presentation Management
- `create_presentation` - Create new presentations
- `get_presentation` - Get presentation content and metadata
- `update_presentation` - Update presentation properties
- `delete_presentation` - Delete presentations
- `list_presentations` - List available presentations

### Slide Management
- `create_slide` - Create new slides
- `get_slide` - Get slide information
- `update_slide` - Update slide properties
- `delete_slide` - Delete slides
- `list_slides` - List slides in presentation

### Shape Operations
- `create_shape` - Create shapes and text boxes
- `update_shape` - Update shape properties
- `delete_shape` - Delete shapes
- `list_shapes` - List shapes on slide

### Image Operations
- `insert_image` - Insert images into slides
- `update_image` - Update image properties
- `delete_image` - Delete images
- `list_images` - List images on slide

### Table Operations
- `create_table` - Create tables
- `update_table` - Update table content
- `delete_table` - Delete tables
- `list_tables` - List tables on slide

## Usage

The Google Slides API simulation provides a realistic environment for testing presentation-related workflows. All functions return simulated data that mimics real Google Slides API responses, allowing developers to test their Slides integration code without requiring actual Google Slides access.

## Features

### Presentation Management
- Full CRUD operations for presentations
- Presentation metadata management
- Presentation sharing and permissions
- Version history support

### Slide Operations
- Multiple slide support
- Slide creation and deletion
- Slide property management
- Slide layout management

### Content Management
- Text box creation and management
- Shape creation and manipulation
- Image insertion and management
- Table creation and management

### Design Features
- Theme and template support
- Color scheme management
- Font and typography control
- Layout and positioning

### Integration Features
- Real-time collaboration support
- Presentation export capabilities
- Template management
- Comment and suggestion handling

## Error Handling

The module includes comprehensive error simulation that can be configured to test various error scenarios, including authentication errors, permission denied errors, and service-specific errors.

## Testing

The module includes a comprehensive test suite in the `tests/` directory that validates the functionality of all Google Slides service simulations.

## Dependencies

- `common_utils` - Shared utilities for error handling and simulation
- `SimulationEngine` - Database and state management for simulations

## Content Types Supported

The simulation supports various content types:
- **Text**: Headers, body text, and captions
- **Shapes**: Rectangles, circles, arrows, and custom shapes
- **Images**: JPG, PNG, GIF, and SVG formats
- **Tables**: Data tables with formatting
- **Charts**: Embedded charts and graphs
- **Media**: Videos and audio content

## Slide Layouts

The simulation supports various slide layouts:
- **Title Slide**: Presentation title and subtitle
- **Title and Content**: Title with content area
- **Section Header**: Section divider slides
- **Two Content**: Side-by-side content areas
- **Comparison**: Comparison layout
- **Content with Caption**: Content with caption area
- **Blank**: Empty slide for custom content

## Animation Support

The simulation includes support for slide animations:
- **Entrance Animations**: Fade, slide, zoom effects
- **Exit Animations**: Exit effects for elements
- **Emphasis Animations**: Highlight and emphasis effects
- **Motion Paths**: Custom movement animations 