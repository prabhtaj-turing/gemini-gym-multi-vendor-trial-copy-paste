# Phone API Simulation

This package provides a comprehensive simulation of the Phone API functionality, enabling testing and development of phone-related workflows without requiring actual phone access.

## Overview

The Phone API simulation includes modules for call management, phone operations, and communication features. It provides a realistic environment for testing phone integration functionality.

## Components

### Calls Resource
- **Call Management**: Make, receive, and manage phone calls
- **Call Operations**: 
  - Initiate outgoing calls
  - Handle incoming calls
  - Manage call status and duration
  - Handle call transfers
  - Manage call history

### Phone Operations
- **Phone Management**: Manage phone settings and features
- **Phone Operations**:
  - Get phone information
  - Manage phone settings
  - Handle phone features
  - Manage call logs

## Key Functions

### Call Management
- `make_call` - Initiate outgoing calls
- `answer_call` - Answer incoming calls
- `end_call` - End active calls
- `get_call` - Get call details
- `list_calls` - List call history
- `transfer_call` - Transfer calls
- `hold_call` - Put calls on hold
- `resume_call` - Resume held calls
- `mute_call` - Mute/unmute calls
- `add_call` - Add call to conference

### Phone Operations
- `get_phone_info` - Get phone information
- `get_call_logs` - Get call history
- `update_phone_settings` - Update phone settings
- `get_phone_status` - Get phone status

## Usage

The Phone API simulation provides a realistic environment for testing phone-related workflows. All functions return simulated data that mimics real phone API responses, allowing developers to test their phone integration code without requiring actual phone access.

## Features

### Call Features
- Outgoing call initiation
- Incoming call handling
- Call status tracking
- Call duration management
- Call transfer capabilities
- Conference call support

### Phone Features
- Phone information retrieval
- Call history management
- Phone settings management
- Call log tracking
- Phone status monitoring

### Integration Features
- Real-time call status updates
- Call event notifications
- Call quality monitoring
- Call analytics and reporting

## Error Handling

The module includes comprehensive error simulation that can be configured to test various error scenarios, including network failures, call failures, busy signals, and service-specific errors.

## Testing

The module includes a comprehensive test suite in the `tests/` directory that validates the functionality of all Phone service simulations.

## Dependencies

- `common_utils` - Shared utilities for error handling and simulation
- `SimulationEngine` - Database and state management for simulations

## Call Types Supported

The simulation supports various call types:
- **Voice Calls**: Standard voice calls
- **Video Calls**: Video call support
- **Conference Calls**: Multi-party calls
- **Emergency Calls**: Emergency call handling
- **International Calls**: International calling support

## Call Status Types

The simulation tracks various call statuses:
- **Ringing**: Incoming call notification
- **Connected**: Active call in progress
- **On Hold**: Call temporarily suspended
- **Transferring**: Call being transferred
- **Ended**: Call completed or terminated
- **Missed**: Unanswered incoming call
- **Rejected**: Declined incoming call

## Phone Features

The simulation supports various phone features:
- **Caller ID**: Display caller information
- **Call Waiting**: Handle multiple incoming calls
- **Call Forwarding**: Forward calls to other numbers
- **Voicemail**: Voicemail message handling
- **Conference Calling**: Multi-party call support
- **Call Recording**: Call recording capabilities 