# WhatsApp API Simulation

This package provides a comprehensive simulation of the WhatsApp API functionality, enabling testing and development of messaging workflows without requiring actual WhatsApp access.

## ⚠️ Important: Phone Number Format Requirements

**The WhatsApp API has inconsistent phone number format requirements across different methods. This is a known limitation that requires careful attention.**

### Methods Requiring E.164 Format (with +):
- `get_direct_chat_by_contact(sender_phone_number)` - Expects: `"+14155552671"`
- `list_messages(sender_phone_number)` - Expects: `"+14155552671"`

### Methods Requiring Digits-Only Format (no +):
- `send_message(recipient)` - Expects: `"14155552671"`
- `send_audio_message(recipient)` - Expects: `"14155552671"`
- `send_file(recipient)` - Expects: `"14155552671"`



### Common Error Scenarios:
- ❌ `get_direct_chat_by_contact("14155552671")` - Will fail (missing +)
- ❌ `send_message("+14155552671", "Hello")` - Will fail (has +)
- ✅ `get_direct_chat_by_contact("+14155552671")` - Correct
- ✅ `send_message("14155552671", "Hello")` - Correct



### Troubleshooting Phone Number Format Errors:

**Error: "Invalid phone number format"**
- **Cause**: Wrong format for the specific method
- **Solution**: Ensure correct format based on method requirements

**Error: "The provided phone number has an invalid format"**
- **Cause**: Missing + for methods that require E.164 format
- **Solution**: Add + prefix: `"+14155552671"`

**Error: "InvalidRecipientError"**
- **Cause**: Including + for methods that require digits-only format
- **Solution**: Remove + prefix: `"14155552671"`

## Overview

The WhatsApp API simulation includes modules for message management, chat operations, contact management, and media handling. It provides a realistic environment for testing WhatsApp integration functionality.

## Components

### Messages Resource
- **Message Management**: Send, read, update, delete messages
- **Message Operations**: 
  - Send text, media, and template messages
  - Get message status and delivery reports
  - Reply to messages
  - Forward messages
  - Handle message reactions

### Chats Resource
- **Chat Management**: Manage conversations and chat sessions
- **Chat Operations**:
  - Create and manage chats
  - Get chat information and history
  - Update chat properties
  - Handle group chats
  - Manage chat participants

### Contacts Resource
- **Contact Management**: Manage contact information
- **Contact Operations**:
  - Create and update contacts
  - Get contact details
  - List contacts
  - Manage contact groups
  - Handle contact synchronization

### Media Resource
- **Media Management**: Handle media files and attachments
- **Media Operations**:
  - Upload and download media
  - Get media information
  - Delete media files
  - Handle media types (images, videos, audio, documents)

## Key Functions

### Message Management
- `send_message` - Send text messages
- `send_media_message` - Send media messages
- `send_template_message` - Send template messages
- `get_message` - Get message details
- `list_messages` - List chat messages
- `update_message` - Update message content
- `delete_message` - Delete messages
- `reply_to_message` - Reply to specific messages
- `forward_message` - Forward messages to other chats

### Chat Management
- `create_chat` - Create new chat sessions
- `get_chat` - Get chat information
- `list_chats` - List available chats
- `update_chat` - Update chat properties
- `delete_chat` - Delete chat sessions
- `get_chat_participants` - Get chat participants
- `add_chat_participant` - Add participants to group chats
- `remove_chat_participant` - Remove participants from group chats

### Contact Management
- `create_contact` - Create new contacts
- `get_contact` - Get contact details
- `list_contacts` - List all contacts
- `update_contact` - Update contact information
- `delete_contact` - Delete contacts
- `search_contacts` - Search for contacts
- `get_contact_groups` - Get contact groups

### Media Management
- `upload_media` - Upload media files
- `download_media` - Download media files
- `get_media` - Get media information
- `delete_media` - Delete media files
- `list_media` - List media in chat

## Usage

The WhatsApp API simulation provides a realistic environment for testing messaging workflows. All functions return simulated data that mimics real WhatsApp API responses, allowing developers to test their WhatsApp integration code without requiring actual WhatsApp access.

## Features

### Message Features
- Text message support
- Media message support (images, videos, audio, documents)
- Template message support
- Message status tracking
- Delivery reports
- Message reactions

### Chat Features
- Individual and group chat support
- Chat history management
- Participant management
- Chat metadata handling
- Real-time chat simulation

### Contact Features
- Contact creation and management
- Contact synchronization
- Contact group management
- Contact search and filtering
- Contact metadata handling

### Media Features
- Multiple media type support
- Media upload and download
- Media metadata management
- Media file organization
- Media sharing capabilities

### Integration Features
- Webhook support for real-time updates
- Message queuing and delivery
- Contact synchronization
- Media file management
- Template message system

## Error Handling

The module includes comprehensive error simulation that can be configured to test various error scenarios, including authentication errors, network failures, media upload errors, and service-specific errors.

## Testing

The module includes a comprehensive test suite in the `tests/` directory that validates the functionality of all WhatsApp service simulations.

## Dependencies

- `common_utils` - Shared utilities for error handling and simulation
- `SimulationEngine` - Database and state management for simulations

## Message Types Supported

The simulation supports various message types:
- **Text Messages**: Plain text and formatted text
- **Media Messages**: Images, videos, audio, documents
- **Template Messages**: Pre-approved message templates
- **Location Messages**: Location sharing
- **Contact Messages**: Contact sharing
- **Sticker Messages**: Sticker and GIF support

## Media Types Supported

The simulation supports various media types:
- **Images**: JPG, PNG, GIF, WebP formats
- **Videos**: MP4, AVI, MOV, 3GP formats
- **Audio**: MP3, WAV, OGG, M4A formats
- **Documents**: PDF, DOC, XLS, PPT formats
- **Archives**: ZIP, RAR formats

## Chat Types

The simulation supports various chat types:
- **Individual Chats**: One-on-one conversations
- **Group Chats**: Multi-participant conversations
- **Broadcast Lists**: One-to-many messaging
- **Business Chats**: Business account conversations 