# Google People API Simulation

This package provides a comprehensive simulation of the Google People API functionality, enabling testing and development of people management workflows without requiring actual Google People access.

## Overview

The Google People API simulation includes modules for people management, contact groups, other contacts, and people data handling. It provides a realistic environment for testing Google People integration functionality.

## Components

### People Resource
- **People Management**: Create, read, update, delete people profiles
- **People Operations**: 
  - Create and manage people profiles
  - Get people details and metadata
  - Update people information
  - Delete people profiles
  - Search and filter people

### Contact Groups Resource
- **Group Management**: Manage contact groups and categories
- **Group Operations**:
  - Create and manage contact groups
  - Get group details and members
  - Update group information
  - Delete contact groups
  - Manage group memberships

### Other Contacts Resource
- **Other Contacts Management**: Handle external and imported contacts
- **Other Contacts Operations**:
  - Manage external contact sources
  - Handle imported contact data
  - Manage contact synchronization
  - Handle contact merging

## Key Functions

### People Management
- `create_person` - Create new people profiles
- `get_person` - Get people details
- `list_people` - List all people
- `update_person` - Update people information
- `delete_person` - Delete people profiles
- `search_people` - Search for people
- `get_people_connections` - Get people connections

### Contact Groups Management
- `create_contact_group` - Create contact groups
- `get_contact_group` - Get group details
- `list_contact_groups` - List all groups
- `update_contact_group` - Update group information
- `delete_contact_group` - Delete contact groups
- `add_person_to_group` - Add people to groups
- `remove_person_from_group` - Remove people from groups

### Other Contacts Management
- `get_other_contacts` - Get other contacts
- `list_other_contacts` - List other contacts
- `update_other_contact` - Update other contact information
- `delete_other_contact` - Delete other contacts
- `sync_other_contacts` - Synchronize other contacts

### People Data Operations
- `add_person_phone` - Add phone numbers to people
- `update_person_phone` - Update people phone numbers
- `delete_person_phone` - Delete people phone numbers
- `add_person_email` - Add email addresses to people
- `update_person_email` - Update people email addresses
- `delete_person_email` - Delete people email addresses
- `add_person_address` - Add addresses to people
- `update_person_address` - Update people addresses
- `delete_person_address` - Delete people addresses

## Usage

The Google People API simulation provides a realistic environment for testing people management workflows. All functions return simulated data that mimics real Google People API responses, allowing developers to test their People integration code without requiring actual Google People access.

## Features

### People Management
- Full CRUD operations for people profiles
- People metadata management
- People photo and avatar support
- People organization and grouping
- People search and filtering

### Contact Groups
- Contact group creation and management
- Group member management
- Group categorization and organization
- Group sharing and permissions
- Group synchronization

### Other Contacts
- External contact source management
- Imported contact data handling
- Contact synchronization features
- Contact merging capabilities
- Contact deduplication

### People Data Support
- Multiple phone numbers per person
- Multiple email addresses per person
- Multiple addresses per person
- People notes and metadata
- People photos and avatars
- Social media profiles

### Integration Features
- Real-time people updates
- People change notifications
- People backup and restore
- People sharing capabilities
- People analytics and reporting

## Error Handling

The module includes comprehensive error simulation that can be configured to test various error scenarios, including authentication errors, data validation errors, and service-specific errors.

## Testing

The module includes a comprehensive test suite in the `tests/` directory that validates the functionality of all Google People service simulations.

## Dependencies

- `common_utils` - Shared utilities for error handling and simulation
- `SimulationEngine` - Database and state management for simulations

## People Data Types

The simulation supports various people data types:
- **Names**: First, middle, and last names
- **Phone Numbers**: Mobile, home, work, and other phone types
- **Email Addresses**: Personal, work, and other email types
- **Addresses**: Home, work, and other address types
- **Dates**: Birthdays, anniversaries, and other important dates
- **Photos**: People photos and avatars
- **Notes**: People notes and additional information
- **Social Media**: Social media profiles and handles

## Contact Group Types

The simulation supports various group types:
- **Custom Groups**: User-defined contact groups
- **System Groups**: System-managed groups (family, work, etc.)
- **Smart Groups**: Automatically populated groups based on criteria
- **Shared Groups**: Groups shared with other users
- **Google Groups**: Google Workspace groups

## People Properties

The simulation handles various people properties:
- **Basic Information**: Name, phone, email, address
- **Extended Information**: Company, job title, website
- **Social Media**: Social media profiles and handles
- **Custom Fields**: User-defined people fields
- **Metadata**: Creation date, modification date, source
- **Relationships**: Family, work, and social relationships 