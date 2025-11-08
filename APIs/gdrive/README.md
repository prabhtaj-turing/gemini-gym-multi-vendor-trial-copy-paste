# Google Drive API Simulation

This package provides a comprehensive simulation of the Google Drive API functionality, enabling testing and development of file storage and management workflows without requiring actual Google Drive access.

## Overview

The Google Drive API simulation includes modules for file management, drive management, permissions, comments, replies, changes tracking, and app management. It provides a realistic environment for testing Google Drive integration functionality.

## Components

### Files Resource
- **File Management**: Create, read, update, delete files and folders
- **File Operations**: 
  - Upload and download files
  - Copy and move files
  - Search and list files
  - Manage file metadata
  - Handle file permissions

### Drives Resource
- **Drive Management**: Manage shared drives
- **Drive Operations**:
  - Create and delete shared drives
  - List available drives
  - Manage drive members
  - Handle drive permissions

### Permissions Resource
- **Permission Management**: Manage file and folder permissions
- **Permission Operations**:
  - Grant and revoke access
  - Manage user and group permissions
  - Handle sharing settings
  - Control inheritance

### Comments Resource
- **Comment Management**: Add and manage file comments
- **Comment Operations**:
  - Create and edit comments
  - List file comments
  - Reply to comments
  - Manage comment threads

### Replies Resource
- **Reply Management**: Handle comment replies
- **Reply Operations**:
  - Create replies to comments
  - Update and delete replies
  - List comment replies

### Changes Resource
- **Change Tracking**: Monitor file and folder changes
- **Change Operations**:
  - List file changes
  - Track modification history
  - Handle change notifications
  - Manage change tokens

### About Resource
- **Account Information**: Get user and account details
- **Quota Management**: Monitor storage usage
- **Feature Information**: Get available features

### Apps Resource
- **App Management**: Manage installed applications
- **App Operations**:
  - List installed apps
  - Get app information
  - Manage app permissions

### Channels Resource
- **Notification Management**: Handle webhook notifications
- **Channel Operations**:
  - Create notification channels
  - Stop notification channels
  - Manage webhook subscriptions

## Key Functions

### File Management
- `create_file` - Create new files and folders
- `get_file` - Get file metadata and content
- `update_file` - Update file content and metadata
- `delete_file` - Delete files and folders
- `list_files` - List files and folders
- `copy_file` - Copy files and folders
- `move_file` - Move files and folders
- `search_files` - Search for files

### Drive Management
- `create_drive` - Create shared drives
- `get_drive` - Get drive information
- `list_drives` - List available drives
- `delete_drive` - Delete shared drives

### Permission Management
- `create_permission` - Grant file permissions
- `get_permission` - Get permission details
- `list_permissions` - List file permissions
- `update_permission` - Update permissions
- `delete_permission` - Revoke permissions

### Comment Management
- `create_comment` - Add comments to files
- `get_comment` - Get comment details
- `list_comments` - List file comments
- `update_comment` - Update comments
- `delete_comment` - Delete comments

### Reply Management
- `create_reply` - Reply to comments
- `get_reply` - Get reply details
- `list_replies` - List comment replies
- `update_reply` - Update replies
- `delete_reply` - Delete replies

### Change Tracking
- `list_changes` - List file changes
- `get_change` - Get change details
- `watch_changes` - Watch for changes

### Account Information
- `get_about` - Get account information
- `get_quota` - Get storage quota

### App Management
- `list_apps` - List installed apps
- `get_app` - Get app information

## Usage

The Google Drive API simulation provides a realistic environment for testing file storage and management workflows. All functions return simulated data that mimics real Google Drive API responses, allowing developers to test their Drive integration code without requiring actual Google Drive access.

## Features

### File Management
- Full CRUD operations for files and folders
- File upload and download simulation
- File search and filtering
- File sharing and collaboration
- Version history support

### Drive Management
- Shared drive creation and management
- Drive member management
- Drive permission controls
- Drive organization features

### Collaboration Features
- Real-time collaboration simulation
- Comment and reply system
- Permission management
- Change tracking and notifications

### Integration Features
- Webhook support for real-time updates
- Batch operations for multiple files
- File format support
- Metadata management

## Error Handling

The module includes comprehensive error simulation that can be configured to test various error scenarios, including authentication errors, permission denied errors, quota exceeded errors, and service-specific errors.

## Testing

The module includes a comprehensive test suite in the `tests/` directory that validates the functionality of all Google Drive service simulations.

## Dependencies

- `common_utils` - Shared utilities for error handling and simulation
- `SimulationEngine` - Database and state management for simulations

## File Types Supported

The simulation supports various file types:
- **Documents**: Google Docs, Word, PDF
- **Spreadsheets**: Google Sheets, Excel
- **Presentations**: Google Slides, PowerPoint
- **Images**: JPG, PNG, GIF, SVG
- **Videos**: MP4, AVI, MOV
- **Audio**: MP3, WAV, FLAC
- **Archives**: ZIP, RAR, 7Z
- **Code**: Various programming language files 