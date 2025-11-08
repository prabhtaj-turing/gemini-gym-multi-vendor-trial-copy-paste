# Contacts API Simulation

This package provides a comprehensive simulation of the Contacts API functionality, enabling testing and development of contact management workflows without requiring actual contacts access.

## Overview

The Contacts API simulation includes modules for contact management, contact operations, and contact data handling. It provides a realistic environment for testing contact integration functionality.

## Components

### Contacts Resource
- **Contact Management**: Create, read, update, delete contacts
- **Contact Operations**: 
  - Create and manage contact information
  - Get contact details and metadata
  - Update contact information
  - Delete contacts
  - Search and filter contacts

### Contact Data Management
- **Data Management**: Handle various contact data types
- **Data Operations**:
  - Manage contact names and addresses
  - Handle phone numbers and email addresses
  - Manage contact photos and avatars
  - Handle contact notes and metadata

## Key Functions

### Contact Management
- `create_contact` - Create new contacts
- `get_contact` - Get contact details
- `list_contacts` - List all contacts
- `update_contact` - Update contact information
- `delete_contact` - Delete contacts
- `search_contacts` - Search for contacts
- `get_contact_groups` - Get contact groups

### Contact Data Operations
- `add_contact_phone` - Add phone numbers to contacts
- `update_contact_phone` - Update contact phone numbers
- `delete_contact_phone` - Delete contact phone numbers
- `add_contact_email` - Add email addresses to contacts
- `update_contact_email` - Update contact email addresses
- `delete_contact_email` - Delete contact email addresses
- `add_contact_address` - Add addresses to contacts
- `update_contact_address` - Update contact addresses
- `delete_contact_address` - Delete contact addresses

### Contact Organization
- `create_contact_group` - Create contact groups
- `get_contact_group` - Get group details
- `list_contact_groups` - List all groups
- `update_contact_group` - Update group information
- `delete_contact_group` - Delete contact groups
- `add_contact_to_group` - Add contacts to groups
- `remove_contact_from_group` - Remove contacts from groups

## Usage

The Contacts API simulation provides a realistic environment for testing contact management workflows. All functions return simulated data that mimics real Contacts API responses, allowing developers to test their contact integration code without requiring actual contacts access.

## Features

### Contact Management
- Full CRUD operations for contacts
- Contact metadata management
- Contact photo and avatar support
- Contact organization and grouping
- Contact search and filtering

### Contact Data Support
- Multiple phone numbers per contact
- Multiple email addresses per contact
- Multiple addresses per contact
- Contact notes and metadata
- Contact photos and avatars

### Organization Features
- Contact group creation and management
- Contact categorization
- Contact tagging and labeling
- Contact import and export
- Contact synchronization

### Integration Features
- Real-time contact updates
- Contact change notifications
- Contact backup and restore
- Contact sharing capabilities
- Contact analytics and reporting

## Error Handling

The module includes comprehensive error simulation that can be configured to test various error scenarios, including authentication errors, data validation errors, and service-specific errors.

## Testing

The module includes a comprehensive test suite in the `tests/` directory that validates the functionality of all Contacts service simulations.

## Dependencies

- `common_utils` - Shared utilities for error handling and simulation
- `SimulationEngine` - Database and state management for simulations

## Contact Data Types

The simulation supports various contact data types:
- **Names**: First, middle, and last names
- **Phone Numbers**: Mobile, home, work, and other phone types
- **Email Addresses**: Personal, work, and other email types
- **Addresses**: Home, work, and other address types
- **Dates**: Birthdays, anniversaries, and other important dates
- **Photos**: Contact photos and avatars
- **Notes**: Contact notes and additional information

## Contact Groups

The simulation supports various group types:
- **Custom Groups**: User-defined contact groups
- **System Groups**: System-managed groups (family, work, etc.)
- **Smart Groups**: Automatically populated groups based on criteria
- **Shared Groups**: Groups shared with other users

## Contact Properties

The simulation handles various contact properties:
- **Basic Information**: Name, phone, email, address
- **Extended Information**: Company, job title, website
- **Social Media**: Social media profiles and handles
- **Custom Fields**: User-defined contact fields
- **Metadata**: Creation date, modification date, source 