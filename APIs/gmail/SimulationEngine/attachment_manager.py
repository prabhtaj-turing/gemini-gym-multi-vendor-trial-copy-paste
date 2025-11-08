"""
Gmail API Attachment Manager

Database integration utilities for managing attachments in Gmail API.
Handles attachment operations, payload creation, and database integration.
All functions are standalone for easy importing in endpoints.
"""

import os
import base64
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .db import DB
from .models import AttachmentModel
from .file_utils import encode_file_to_base64, get_mime_type, validate_file_type
from .attachment_utils import (
    create_attachment_from_file,
    create_attachment_from_data,
    get_attachment_from_global_collection,
    generate_attachment_id
)
from .utils import _ensure_user, _next_counter


# Default maximum file size (25MB)
DEFAULT_MAX_SIZE_MB = 25
GMAIL_MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25MB in bytes
GMAIL_MAX_MESSAGE_SIZE = 100 * 1024 * 1024  # 100MB total message size


def validate_attachment_size(file_size: int, filename: str = "") -> None:
    """
    Validate attachment size against Gmail limits.
    
    Args:
        file_size: Size of the attachment in bytes
        filename: Name of the file (for error messages)
        
    Raises:
        ValueError: If attachment exceeds size limits
    """
    if file_size > GMAIL_MAX_ATTACHMENT_SIZE:
        size_mb = file_size / (1024 * 1024)
        max_mb = GMAIL_MAX_ATTACHMENT_SIZE / (1024 * 1024)
        raise ValueError(
            f"Attachment '{filename}' size ({size_mb:.1f}MB) exceeds Gmail's {max_mb}MB limit"
        )


def _get_attachment_references() -> Dict[str, int]:
    """
    Count references to each attachment across all messages and drafts.
    
    Returns:
        Dictionary mapping attachment_id -> reference_count
    """
    reference_counts = {}
    
    # Count references in messages
    for user_id, user_data in DB.get("users", {}).items():
        # Check messages
        for message in user_data.get("messages", {}).values():
            if "payload" in message and "parts" in message["payload"]:
                for part in message["payload"]["parts"]:
                    att_id = part.get("body", {}).get("attachmentId")
                    if att_id:
                        reference_counts[att_id] = reference_counts.get(att_id, 0) + 1
        
        # Check drafts
        for draft in user_data.get("drafts", {}).values():
            message = draft.get("message", {})
            if "payload" in message and "parts" in message["payload"]:
                for part in message["payload"]["parts"]:
                    att_id = part.get("body", {}).get("attachmentId")
                    if att_id:
                        reference_counts[att_id] = reference_counts.get(att_id, 0) + 1
    
    return reference_counts


def cleanup_unreferenced_attachments() -> int:
    """
    Remove attachments that are no longer referenced by any message or draft.
    
    Returns:
        Number of attachments cleaned up
    """
    if "attachments" not in DB:
        return 0
    
    reference_counts = _get_attachment_references()
    orphaned_attachments = []
    
    # Find attachments with zero references
    for attachment_id in DB["attachments"].keys():
        if reference_counts.get(attachment_id, 0) == 0:
            orphaned_attachments.append(attachment_id)
    
    # Remove orphaned attachments
    for attachment_id in orphaned_attachments:
        del DB["attachments"][attachment_id]
        _update_attachment_counter(-1)
    
    return len(orphaned_attachments)


def get_attachment_reference_count(attachment_id: str) -> int:
    """
    Get the number of references to a specific attachment.
    
    Args:
        attachment_id: The attachment ID to check
        
    Returns:
        Number of references to this attachment
    """
    reference_counts = _get_attachment_references()
    return reference_counts.get(attachment_id, 0)


def cleanup_attachments_for_message(user_id: str, message_id: str) -> int:
    """
    Clean up attachments when a message is deleted.
    Only removes attachments that are no longer referenced elsewhere.
    
    Args:
        user_id: User ID
        message_id: Message ID being deleted
        
    Returns:
        Number of attachments cleaned up
    """
    _ensure_user(user_id)
    
    if message_id not in DB["users"][user_id]["messages"]:
        return 0
    
    message = DB["users"][user_id]["messages"][message_id]
    affected_attachments = set()
    
    # Collect attachment IDs from this message
    if "payload" in message and "parts" in message["payload"]:
        for part in message["payload"]["parts"]:
            att_id = part.get("body", {}).get("attachmentId")
            if att_id:
                affected_attachments.add(att_id)
    
    # If no attachments, nothing to clean up
    if not affected_attachments:
        return 0
    
    # Get current reference counts
    reference_counts = _get_attachment_references()
    cleaned_count = 0
    
    # Check each attachment - if it only has 1 reference (this message), it can be deleted
    for attachment_id in affected_attachments:
        if reference_counts.get(attachment_id, 0) <= 1:
            if attachment_id in DB.get("attachments", {}):
                del DB["attachments"][attachment_id]
                _update_attachment_counter(-1)
                cleaned_count += 1
    
    return cleaned_count


def cleanup_attachments_for_draft(user_id: str, draft_id: str) -> int:
    """
    Clean up attachments when a draft is deleted.
    Only removes attachments that are no longer referenced elsewhere.
    
    Args:
        user_id: User ID
        draft_id: Draft ID being deleted
        
    Returns:
        Number of attachments cleaned up
    """
    _ensure_user(user_id)
    
    if draft_id not in DB["users"][user_id]["drafts"]:
        return 0
    
    draft = DB["users"][user_id]["drafts"][draft_id]
    message = draft.get("message", {})
    affected_attachments = set()
    
    # Collect attachment IDs from this draft
    if "payload" in message and "parts" in message["payload"]:
        for part in message["payload"]["parts"]:
            att_id = part.get("body", {}).get("attachmentId")
            if att_id:
                affected_attachments.add(att_id)
    
    # If no attachments, nothing to clean up
    if not affected_attachments:
        return 0
    
    # Get current reference counts
    reference_counts = _get_attachment_references()
    cleaned_count = 0
    
    # Check each attachment - if it only has 1 reference (this draft), it can be deleted
    for attachment_id in affected_attachments:
        if reference_counts.get(attachment_id, 0) <= 1:
            if attachment_id in DB.get("attachments", {}):
                del DB["attachments"][attachment_id]
                _update_attachment_counter(-1)
                cleaned_count += 1
    
    return cleaned_count


def store_attachment_in_db(attachment: Dict[str, Any]) -> None:
    """
    Store attachment in the global attachments collection.
    Now includes size validation.
    
    Args:
        attachment: Attachment dictionary with all metadata and data
        
    Raises:
        ValueError: If attachment exceeds size limits
    """
    # Validate attachment structure
    AttachmentModel(**attachment)
    
    # Validate size limits
    file_size = attachment.get("fileSize", 0)
    filename = attachment.get("filename", "attachment")
    validate_attachment_size(file_size, filename)
    
    # Store in global attachments collection
    DB["attachments"][attachment["attachmentId"]] = attachment
    
    # Update counter
    _update_attachment_counter(1)


def create_payload_with_attachments(
    body_text: str,
    attachment_ids: List[str],
    mime_type: str = "text/plain"
) -> Dict[str, Any]:
    """
    Create Gmail API-compliant payload structure with attachment references.
    Now includes total message size validation.
    
    Args:
        body_text: The message body text
        attachment_ids: List of attachment IDs to reference
        mime_type: MIME type for the body text
        
    Returns:
        Payload dictionary with parts structure
        
    Raises:
        ValueError: If total message size exceeds Gmail limits
    """
    # Encode body text to base64
    body_data = base64.b64encode(body_text.encode('utf-8')).decode('utf-8')
    
    # Calculate total size
    total_size = len(body_text.encode('utf-8'))
    
    # Create base payload with text part
    payload = {
        "mimeType": "multipart/mixed" if attachment_ids else mime_type,
        "parts": [
            {
                "mimeType": mime_type,
                "body": {
                    "data": body_data
                }
            }
        ]
    }
    
    # Add attachment parts if any exist
    if attachment_ids:
        for att_id in attachment_ids:
            attachment = get_attachment_from_global_collection(att_id)
            if attachment:
                attachment_size = attachment.get("fileSize", 0)
                total_size += attachment_size
                
                # Validate total message size
                if total_size > GMAIL_MAX_MESSAGE_SIZE:
                    total_mb = total_size / (1024 * 1024)
                    max_mb = GMAIL_MAX_MESSAGE_SIZE / (1024 * 1024)
                    raise ValueError(
                        f"Total message size ({total_mb:.1f}MB) exceeds Gmail's {max_mb}MB limit"
                    )
                
                attachment_part = {
                    "mimeType": attachment["mimeType"],
                    "filename": attachment["filename"],
                    "body": {
                        "attachmentId": att_id,
                        "size": attachment["fileSize"]
                    }
                }
                payload["parts"].append(attachment_part)
    
    return payload


def create_message_payload_from_files(
    body_text: str,
    file_paths: List[str],
    subject: Optional[str] = None,
    to: Optional[str] = None,
    from_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create complete message payload from file paths.
    Handles file processing, attachment storage, and payload creation.
    
    Args:
        body_text: The message body text
        file_paths: List of file paths to attach
        subject: Email subject
        to: Recipient email
        from_email: Sender email
        
    Returns:
        Complete message dictionary with payload structure
        
    Raises:
        FileNotFoundError: If any file doesn't exist
        ValueError: If any file is invalid or too large
    """
    attachment_ids = []
    
    # Process each file and store as attachment
    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not validate_file_type(file_path):
            raise ValueError(f"Unsupported file type: {file_path}")
        
        # Create attachment from file
        attachment = create_attachment_from_file(file_path)
        
        # Store in database
        store_attachment_in_db(attachment)
        
        attachment_ids.append(attachment["attachmentId"])
    
    # Create payload with attachments
    payload = create_payload_with_attachments(body_text, attachment_ids)
    
    # Add headers if provided
    if subject or to or from_email:
        payload["headers"] = []
        if subject:
            payload["headers"].append({"name": "Subject", "value": subject})
        if to:
            payload["headers"].append({"name": "To", "value": to})
        if from_email:
            payload["headers"].append({"name": "From", "value": from_email})
    
    return payload


def add_attachment_to_message_payload(
    user_id: str,
    message_id: str,
    file_path: str,
    attachment_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add attachment to existing message and update payload structure.
    
    Args:
        user_id: User ID
        message_id: Message ID
        file_path: Path to file to attach
        attachment_id: Optional custom attachment ID
        
    Returns:
        Created attachment dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If user/message doesn't exist or file is invalid
    """
    # Validate inputs
    _ensure_user(user_id)
    
    if message_id not in DB["users"][user_id]["messages"]:
        raise ValueError(f"Message {message_id} not found for user {user_id}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not validate_file_type(file_path):
        raise ValueError(f"Unsupported file type: {file_path}")
    
    # Create attachment from file
    attachment = create_attachment_from_file(file_path, attachment_id)
    
    # Store attachment in global collection
    store_attachment_in_db(attachment)
    
    # Update message payload structure
    message = DB["users"][user_id]["messages"][message_id]
    
    if "payload" not in message:
        # Create initial payload if doesn't exist
        message["payload"] = create_payload_with_attachments(
            message.get("body", ""), 
            [attachment["attachmentId"]]
        )
    else:
        # Add attachment part to existing payload
        if "parts" not in message["payload"]:
            # Convert single-part to multi-part
            body_data = message["payload"].get("body", {}).get("data", "")
            message["payload"] = {
                "mimeType": "multipart/mixed",
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": body_data}
                    }
                ]
            }
        
        # Add attachment part
        attachment_part = {
            "mimeType": attachment["mimeType"],
            "filename": attachment["filename"],
            "body": {
                "attachmentId": attachment["attachmentId"],
                "size": attachment["fileSize"]
            }
        }
        message["payload"]["parts"].append(attachment_part)
        message["payload"]["mimeType"] = "multipart/mixed"
    
    return attachment


def add_attachment_to_draft_payload(
    user_id: str,
    draft_id: str,
    file_path: str,
    attachment_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add attachment to existing draft and update payload structure.
    
    Args:
        user_id: User ID
        draft_id: Draft ID
        file_path: Path to file to attach
        attachment_id: Optional custom attachment ID
        
    Returns:
        Created attachment dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If user/draft doesn't exist or file is invalid
    """
    # Validate inputs
    _ensure_user(user_id)
    
    if draft_id not in DB["users"][user_id]["drafts"]:
        raise ValueError(f"Draft {draft_id} not found for user {user_id}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not validate_file_type(file_path):
        raise ValueError(f"Unsupported file type: {file_path}")
    
    # Create attachment from file
    attachment = create_attachment_from_file(file_path, attachment_id)
    
    # Store attachment in global collection
    store_attachment_in_db(attachment)
    
    # Update draft message payload structure
    draft = DB["users"][user_id]["drafts"][draft_id]
    message = draft.get("message", {})
    
    if "payload" not in message:
        # Create initial payload if doesn't exist
        message["payload"] = create_payload_with_attachments(
            message.get("body", ""), 
            [attachment["attachmentId"]]
        )
    else:
        # Add attachment part to existing payload
        if "parts" not in message["payload"]:
            # Convert single-part to multi-part
            body_data = message["payload"].get("body", {}).get("data", "")
            message["payload"] = {
                "mimeType": "multipart/mixed",
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": body_data}
                    }
                ]
            }
        
        # Add attachment part
        attachment_part = {
            "mimeType": attachment["mimeType"],
            "filename": attachment["filename"],
            "body": {
                "attachmentId": attachment["attachmentId"],
                "size": attachment["fileSize"]
            }
        }
        message["payload"]["parts"].append(attachment_part)
        message["payload"]["mimeType"] = "multipart/mixed"
    
    return attachment


def add_attachment_data_to_message(
    user_id: str,
    message_id: str,
    data: Union[str, bytes],
    filename: str,
    mime_type: Optional[str] = None,
    attachment_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add attachment from raw data to existing message.
    
    Args:
        user_id: User ID
        message_id: Message ID
        data: File content (string or bytes)
        filename: Name for the attachment
        mime_type: MIME type (auto-detected if None)
        attachment_id: Optional custom attachment ID
        
    Returns:
        Created attachment dictionary
    """
    # Validate inputs
    _ensure_user(user_id)
    
    if message_id not in DB["users"][user_id]["messages"]:
        raise ValueError(f"Message {message_id} not found for user {user_id}")
    
    # Create attachment from data
    attachment = create_attachment_from_data(data, filename, mime_type, attachment_id)
    
    # Store attachment in global collection
    store_attachment_in_db(attachment)
    
    # Update message payload (similar logic as file-based)
    message = DB["users"][user_id]["messages"][message_id]
    
    if "payload" not in message:
        message["payload"] = create_payload_with_attachments(
            message.get("body", ""), 
            [attachment["attachmentId"]]
        )
    else:
        if "parts" not in message["payload"]:
            body_data = message["payload"].get("body", {}).get("data", "")
            message["payload"] = {
                "mimeType": "multipart/mixed",
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": body_data}
                    }
                ]
            }
        
        attachment_part = {
            "mimeType": attachment["mimeType"],
            "filename": attachment["filename"],
            "body": {
                "attachmentId": attachment["attachmentId"],
                "size": attachment["fileSize"]
            }
        }
        message["payload"]["parts"].append(attachment_part)
        message["payload"]["mimeType"] = "multipart/mixed"
    
    return attachment


def remove_attachment_from_message(
    user_id: str,
    message_id: str,
    attachment_id: str
) -> bool:
    """
    Remove attachment from message and update payload structure.
    
    Args:
        user_id: User ID
        message_id: Message ID
        attachment_id: Attachment ID to remove
        
    Returns:
        True if successfully removed, False if not found
    """
    _ensure_user(user_id)
    
    if message_id not in DB["users"][user_id]["messages"]:
        return False
    
    message = DB["users"][user_id]["messages"][message_id]
    
    if "payload" in message and "parts" in message["payload"]:
        # Remove attachment part from payload
        original_parts = message["payload"]["parts"]
        message["payload"]["parts"] = [
            part for part in original_parts 
            if part.get("body", {}).get("attachmentId") != attachment_id
        ]
        
        # If only text part remains, convert back to single-part
        if len(message["payload"]["parts"]) == 1:
            text_part = message["payload"]["parts"][0]
            if text_part.get("mimeType") == "text/plain":
                message["payload"] = {
                    "mimeType": "text/plain",
                    "body": text_part["body"]
                }
        
        return len(original_parts) > len(message["payload"].get("parts", []))
    
    return False


def get_attachment_by_id(attachment_id: str) -> Optional[Dict[str, Any]]:
    """
    Get attachment by ID from global collection.
    
    Args:
        attachment_id: Attachment ID
        
    Returns:
        Attachment dictionary or None if not found
    """
    return get_attachment_from_global_collection(attachment_id)


def get_attachment_metadata(attachment_id: str) -> Optional[Dict[str, Any]]:
    """
    Get attachment metadata (without data field).
    
    Args:
        attachment_id: Attachment ID
        
    Returns:
        Attachment metadata dictionary or None if not found
    """
    attachment = get_attachment_from_global_collection(attachment_id)
    if not attachment:
        return None
    
    # Return metadata without data field
    metadata = attachment.copy()
    metadata.pop("data", None)
    return metadata


def list_message_attachments(
    user_id: str,
    message_id: str,
    include_data: bool = False
) -> List[Dict[str, Any]]:
    """
    List all attachments for a message.
    
    Args:
        user_id: User ID
        message_id: Message ID
        include_data: Whether to include base64 data
        
    Returns:
        List of attachment dictionaries
    """
    _ensure_user(user_id)
    
    if message_id not in DB["users"][user_id]["messages"]:
        return []
    
    message = DB["users"][user_id]["messages"][message_id]
    attachments = []
    
    if "payload" in message and "parts" in message["payload"]:
        for part in message["payload"]["parts"]:
            att_id = part.get("body", {}).get("attachmentId")
            if att_id:
                attachment = get_attachment_from_global_collection(att_id)
                if attachment:
                    attachment = attachment.copy()
                    if not include_data:
                        attachment.pop("data", None)
                    attachments.append(attachment)
    
    return attachments


def list_user_attachments(
    user_id: str,
    include_data: bool = False
) -> List[Dict[str, Any]]:
    """
    List all attachments for a user across all messages and drafts.
    
    Args:
        user_id: User ID
        include_data: Whether to include base64 data
        
    Returns:
        List of attachment dictionaries
    """
    _ensure_user(user_id)
    
    user_attachments = []
    attachment_ids = set()
    
    # Collect attachment IDs from messages
    for message in DB["users"][user_id]["messages"].values():
        if "payload" in message and "parts" in message["payload"]:
            for part in message["payload"]["parts"]:
                att_id = part.get("body", {}).get("attachmentId")
                if att_id:
                    attachment_ids.add(att_id)
    
    # Collect attachment IDs from drafts
    for draft in DB["users"][user_id]["drafts"].values():
        message = draft.get("message", {})
        if "payload" in message and "parts" in message["payload"]:
            for part in message["payload"]["parts"]:
                att_id = part.get("body", {}).get("attachmentId")
                if att_id:
                    attachment_ids.add(att_id)
    
    # Fetch actual attachments
    for att_id in attachment_ids:
        attachment = get_attachment_from_global_collection(att_id)
        if attachment:
            attachment = attachment.copy()
            if not include_data:
                attachment.pop("data", None)
            user_attachments.append(attachment)
    
    return user_attachments


def validate_attachment(attachment: Dict[str, Any]) -> bool:
    """
    Validate attachment structure using Pydantic model.
    
    Args:
        attachment: Attachment dictionary
        
    Returns:
        True if valid, False otherwise
    """
    try:
        AttachmentModel(**attachment)
        return True
    except Exception:
        return False


def get_attachment_stats(user_id: str) -> Dict[str, Any]:
    """
    Get attachment statistics for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary with attachment statistics including reference counts
    """
    attachments = list_user_attachments(user_id, include_data=False)
    reference_counts = _get_attachment_references()
    
    total_count = len(attachments)
    total_size = sum(att.get("fileSize", 0) for att in attachments)
    
    # Count by MIME type
    mime_types = {}
    reference_info = {}
    for att in attachments:
        mime_type = att.get("mimeType", "unknown")
        mime_types[mime_type] = mime_types.get(mime_type, 0) + 1
        
        # Add reference count info
        att_id = att.get("attachmentId")
        if att_id:
            reference_info[att_id] = {
                "filename": att.get("filename", ""),
                "size": att.get("fileSize", 0),
                "mimeType": att.get("mimeType", ""),
                "referenceCount": reference_counts.get(att_id, 0)
            }
    
    # Find orphaned attachments (for this user's attachments)
    orphaned_count = sum(1 for att in attachments 
                        if reference_counts.get(att.get("attachmentId"), 0) == 0)
    
    return {
        "totalCount": total_count,
        "totalSize": total_size,
        "averageSize": total_size // total_count if total_count > 0 else 0,
        "mimeTypeBreakdown": mime_types,
        "orphanedCount": orphaned_count,
        "attachmentReferences": reference_info,
        "maxAttachmentSize": GMAIL_MAX_ATTACHMENT_SIZE,
        "maxMessageSize": GMAIL_MAX_MESSAGE_SIZE
    }


def get_global_attachment_stats() -> Dict[str, Any]:
    """
    Get global attachment statistics across all users.
    
    Returns:
        Dictionary with global attachment statistics
    """
    if "attachments" not in DB:
        return {
            "totalAttachments": 0,
            "totalSize": 0,
            "orphanedAttachments": 0,
            "mimeTypeBreakdown": {},
            "referenceCountDistribution": {}
        }
    
    reference_counts = _get_attachment_references()
    total_attachments = len(DB["attachments"])
    total_size = sum(att.get("fileSize", 0) for att in DB["attachments"].values())
    orphaned_count = sum(1 for att_id in DB["attachments"].keys() 
                        if reference_counts.get(att_id, 0) == 0)
    
    # MIME type breakdown
    mime_types = {}
    for att in DB["attachments"].values():
        mime_type = att.get("mimeType", "unknown")
        mime_types[mime_type] = mime_types.get(mime_type, 0) + 1
    
    # Reference count distribution
    ref_distribution = {}
    for count in reference_counts.values():
        ref_distribution[count] = ref_distribution.get(count, 0) + 1
    
    # Add count for orphaned attachments
    if orphaned_count > 0:
        ref_distribution[0] = orphaned_count
    
    return {
        "totalAttachments": total_attachments,
        "totalSize": total_size,
        "averageSize": total_size // total_attachments if total_attachments > 0 else 0,
        "orphanedAttachments": orphaned_count,
        "mimeTypeBreakdown": mime_types,
        "referenceCountDistribution": ref_distribution,
        "storageEfficiency": {
            "referencedAttachments": total_attachments - orphaned_count,
            "wastedStorage": sum(
                DB["attachments"][att_id].get("fileSize", 0) 
                for att_id in DB["attachments"].keys() 
                if reference_counts.get(att_id, 0) == 0
            )
        }
    }


def validate_message_attachments(user_id: str, message_id: str) -> Dict[str, Any]:
    """
    Validate that all attachments referenced in a message exist and are consistent.
    
    Args:
        user_id: User ID
        message_id: Message ID
        
    Returns:
        Dictionary with validation results
    """
    _ensure_user(user_id)
    
    if message_id not in DB["users"][user_id]["messages"]:
        return {"valid": False, "error": "Message not found"}
    
    message = DB["users"][user_id]["messages"][message_id]
    issues = []
    attachment_count = 0
    total_size = 0
    
    if "payload" in message and "parts" in message["payload"]:
        for part in message["payload"]["parts"]:
            att_id = part.get("body", {}).get("attachmentId")
            if att_id:
                attachment_count += 1
                
                # Check if attachment exists in global collection
                if att_id not in DB.get("attachments", {}):
                    issues.append(f"Missing attachment: {att_id}")
                    continue
                
                attachment = DB["attachments"][att_id]
                expected_size = attachment.get("fileSize", 0)
                actual_size = part.get("body", {}).get("size", 0)
                total_size += expected_size
                
                # Check size consistency
                if expected_size != actual_size:
                    issues.append(f"Size mismatch for {att_id}: expected {expected_size}, got {actual_size}")
                
                # Check filename consistency
                part_filename = part.get("filename", "")
                att_filename = attachment.get("filename", "")
                if part_filename != att_filename:
                    issues.append(f"Filename mismatch for {att_id}: part='{part_filename}', attachment='{att_filename}'")
    
    # Check size limits
    if total_size > GMAIL_MAX_MESSAGE_SIZE:
        issues.append(f"Total message size ({total_size} bytes) exceeds limit ({GMAIL_MAX_MESSAGE_SIZE} bytes)")
    
    return {
        "valid": len(issues) == 0,
        "attachmentCount": attachment_count,
        "totalSize": total_size,
        "issues": issues
    }


def _update_attachment_counter(delta: int) -> None:
    """
    Update the global attachment counter.
    
    Args:
        delta: Change in attachment count
    """
    if "counters" not in DB:
        DB["counters"] = {}
    
    if "attachment" not in DB["counters"]:
        DB["counters"]["attachment"] = 0
    
    DB["counters"]["attachment"] += delta


def get_supported_file_types() -> List[str]:
    """
    Get list of supported file extensions.
    
    Returns:
        List of supported file extensions
    """
    from .file_utils import TEXT_EXTENSIONS, BINARY_EXTENSIONS
    return sorted(list(TEXT_EXTENSIONS.union(BINARY_EXTENSIONS)))


def get_supported_mime_types() -> List[str]:
    """
    Get list of supported MIME types.
    
    Returns:
        List of supported MIME types
    """
    from .file_utils import SUPPORTED_MIME_TYPES
    return sorted(list(SUPPORTED_MIME_TYPES)) 