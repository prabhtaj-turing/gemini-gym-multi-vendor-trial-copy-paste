# Google Calendar API Simulation

This package provides a comprehensive simulation of the Google Calendar API functionality, enabling testing and development of calendar-related workflows without requiring actual Google Calendar access.

## Overview

The Google Calendar API simulation includes modules for event management, calendar management, access control, calendar list management, and notification channels. It provides a realistic environment for testing Google Calendar integration functionality.

## Components

### Events Resource
- **Event Management**: Create, read, update, delete calendar events
- **Event Operations**: 
  - List events and event instances
  - Move events between calendars
  - Quick add events
  - Import events
  - Watch event changes

### Calendars Resource
- **Calendar Management**: Create, read, update, delete calendars
- **Calendar Operations**:
  - Get calendar metadata
  - Clear primary calendar
  - Create secondary calendars
  - Update calendar properties

### Access Control (ACL) Resource
- **Permission Management**: Manage access control rules
- **ACL Operations**:
  - Create, read, update, delete access control rules
  - List access control rules
  - Watch ACL changes

### Calendar List Resource
- **Calendar List Management**: Manage calendar list entries
- **List Operations**:
  - Add calendars to user's calendar list
  - Update calendar list properties
  - Remove calendars from list
  - Watch calendar list changes

### Colors Resource
- **Color Management**: Get calendar and event colors
- **Color Operations**: Retrieve available color schemes

### Channels Resource
- **Notification Management**: Manage notification channels
- **Channel Operations**: Stop notification channels

## Key Functions

### Event Management
- `create_event` - Create new calendar events
- `get_event` - Get event details
- `list_events` - List calendar events
- `update_event` - Update event details
- `patch_event` - Partially update events
- `delete_event` - Delete events
- `move_event` - Move events between calendars
- `quick_add_event` - Quick add events
- `import_event` - Import events
- `list_event_instances` - List event instances
- `watch_events` - Watch for event changes

### Calendar Management
- `create_secondary_calendar` - Create secondary calendars
- `get_calendar_metadata` - Get calendar information
- `update_calendar_metadata` - Update calendar properties
- `patch_calendar_metadata` - Partially update calendar
- `delete_secondary_calendar` - Delete secondary calendars
- `clear_primary_calendar` - Clear primary calendar

### Access Control
- `create_access_control_rule` - Create ACL rules
- `get_access_control_rule` - Get ACL rule details
- `list_access_control_rules` - List ACL rules
- `update_access_control_rule` - Update ACL rules
- `patch_access_control_rule` - Partially update ACL rules
- `delete_access_control_rule` - Delete ACL rules
- `watch_access_control_rules` - Watch ACL changes

### Calendar List Management
- `create_calendar_list_entry` - Add calendar to list
- `get_calendar_list_entry` - Get calendar list entry
- `list_calendar_list_entries` - List calendar entries
- `update_calendar_list_entry` - Update calendar list entry
- `patch_calendar_list_entry` - Partially update list entry
- `delete_calendar_list_entry` - Remove calendar from list
- `watch_calendar_list_changes` - Watch list changes

### Colors and Notifications
- `get_calendar_and_event_colors` - Get available colors
- `stop_notification_channel` - Stop notification channels

## Usage

The Google Calendar API simulation provides a realistic environment for testing calendar-related workflows. All functions return simulated data that mimics real Google Calendar API responses, allowing developers to test their calendar integration code without requiring actual Google Calendar access.

## Features

### Event Management
- Full CRUD operations for calendar events
- Event recurrence and series support
- Event attendees and notifications
- Event timezone handling

### Calendar Management
- Primary and secondary calendar support
- Calendar sharing and permissions
- Calendar metadata management
- Calendar color schemes

### Access Control
- Granular permission management
- Role-based access control
- Permission inheritance
- Real-time permission updates

### Integration Features
- Webhook support for real-time updates
- Batch operations for multiple events
- Timezone-aware operations
- Rich text and HTML content support

## Error Handling

The module includes comprehensive error simulation that can be configured to test various error scenarios, including authentication errors, permission denied errors, and service-specific errors.

## Testing

The module includes a comprehensive test suite in the `tests/` directory that validates the functionality of all Google Calendar service simulations.

## Dependencies

- `common_utils` - Shared utilities for error handling and simulation
- `SimulationEngine` - Database and state management for simulations

## Calendar Resources

The module is organized into several resource classes:
- `EventsResource` - Event management operations
- `CalendarsResource` - Calendar management operations
- `AclResource` - Access control operations
- `CalendarListResource` - Calendar list management
- `ColorsResource` - Color scheme operations
- `ChannelsResource` - Notification channel operations 