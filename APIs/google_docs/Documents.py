"""
Document operations for the Google Docs API simulation.

Represents a Google Docs document with methods for document operations.

This class provides methods for creating, retrieving, and updating Google Docs documents,
including handling document content, styles, and collaborative features.

"""

from common_utils.tool_spec_decorator import tool_spec
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone

from .SimulationEngine.models import InsertTextRequestModel, UpdateDocumentStyleRequestModel, DeleteContentRangeRequestModel, ReplaceAllTextRequestModel, InsertTableRequestModel
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _ensure_user, _next_counter
from .SimulationEngine.custom_errors import UserNotFoundError

@tool_spec(
    spec={
        'name': 'get_document',
        'description': 'Get a document by ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'documentId': {
                    'type': 'string',
                    'description': 'The ID of the document to retrieve. Cannot be empty or whitespace.'
                },
                'suggestionsViewMode': {
                    'type': 'string',
                    'description': """ The mode for viewing suggestions.
                    Common values include "DEFAULT_FOR_CURRENT_ACCESS", "SUGGESTIONS_INLINE", "PREVIEW_SUGGESTIONS_ACCEPTED" and "PREVIEW_WITHOUT_SUGGESTIONS".
                    If None, the document's existing setting is preserved. """
                },
                'includeTabsContent': {
                    'type': 'boolean',
                    'description': 'Whether to include tab content. Defaults to False.'
                },
                'userId': {
                    'type': 'string',
                    'description': """ The ID of the user performing the action. Defaults to "me".
                    Cannot be empty or whitespace. """
                }
            },
            'required': [
                'documentId'
            ]
        }
    }
)
def get(
    documentId: str,
    suggestionsViewMode: Optional[str] = None,
    includeTabsContent: Optional[bool] = False,
    userId: Optional[str] = "me",
) -> Dict[str, Any]:
    """Get a document by ID.

    Args:
        documentId (str): The ID of the document to retrieve. Cannot be empty or whitespace.
        suggestionsViewMode (Optional[str]): The mode for viewing suggestions.
            Common values include "DEFAULT_FOR_CURRENT_ACCESS", "SUGGESTIONS_INLINE", "PREVIEW_SUGGESTIONS_ACCEPTED" and "PREVIEW_WITHOUT_SUGGESTIONS".
            If None, the document's existing setting is preserved.
        includeTabsContent (Optional[bool]): Whether to include tab content. Defaults to False.
        userId (Optional[str]): The ID of the user performing the action. Defaults to "me".
            Cannot be empty or whitespace.

    Returns:
        Dict[str, Any]: The document data with the following structure:
                Base document fields:
                - id (str): Unique identifier for the document
                - driveId (str): ID of the drive containing the document (can be empty)
                - name (str): Title/name of the document
                - mimeType (str): MIME type ("application/vnd.google-apps.document")
                - createdTime (str): ISO 8601 timestamp when document was created
                - modifiedTime (str): ISO 8601 timestamp when document was last modified
                - parents (List[str]): List of parent folder IDs
                - owners (List[str]): List of owner email addresses
                - content (List[Dict[str, Any]]): Document content with structure:
                    - elementId (str): Unique identifier for the content element
                    - text (str): Text content of the element
                - tabs (List[Dict[str, Any]]): List of document tabs (usually empty)
                - permissions (List[Dict[str, Any]]): List of permission objects with structure:
                    - role (str): Permission level ("owner", "writer", "reader")
                    - type (str): Permission type ("user", "group", "domain", "anyone")
                    - emailAddress (str): Email address of the user/group
                
                Conditionally added fields:
                - suggestionsViewMode (str): Present if suggestionsViewMode parameter was provided
                - includeTabsContent (bool): Present if includeTabsContent parameter was True
                - comments (Dict[str, Any]): Dictionary of comments associated with this document:
                    - Key: comment ID (str)
                    - Value: Comment object with structure:
                        - id (str): Unique comment identifier
                        - fileId (str): ID of the document this comment belongs to
                        - content (str): Comment text content
                        - author (Dict[str, str]): Author information:
                            - displayName (str): Author's display name
                            - emailAddress (str): Author's email address
                        - createdTime (str): ISO 8601 timestamp when comment was created
                - replies (Dict[str, Any]): Dictionary of replies associated with this document:
                    - Key: reply ID (str)
                    - Value: Reply object with structure:
                        - id (str): Unique reply identifier
                        - commentId (str): ID of the comment this reply belongs to
                        - fileId (str): ID of the document this reply belongs to
                        - content (str): Reply text content
                        - author (Dict[str, str]): Author information:
                            - displayName (str): Author's display name
                            - emailAddress (str): Author's email address
                        - createdTime (str): ISO 8601 timestamp when reply was created
                - labels (Dict[str, Any]): Dictionary of labels associated with this document:
                    - Key: label ID (str)
                    - Value: Label object with structure:
                        - id (str): Unique label identifier
                        - fileId (str): ID of the document this label belongs to
                        - name (str): Label name
                        - color (str): Label color in hex format (e.g., "#FF0000")
                - accessproposals (Dict[str, Any]): Dictionary of access proposals for this document:
                    - Key: proposal ID (str)
                    - Value: Access proposal object with structure:
                        - id (str): Unique proposal identifier
                        - fileId (str): ID of the document this proposal is for
                        - role (str): Requested permission level ("reader", "writer", "owner")
                        - state (str): Proposal state ("pending", "approved", "rejected")
                        - requester (Dict[str, str]): Requester information:
                            - displayName (str): Requester's display name
                            - emailAddress (str): Requester's email address
                        - createdTime (str): ISO 8601 timestamp when proposal was created

    Raises:
        TypeError: If `documentId` is not a string.
        TypeError: If `suggestionsViewMode` is provided and is not a string.
        TypeError: If `includeTabsContent` is not a boolean.
        TypeError: If `userId` is not a string.
        ValueError: If `documentId` or `userId` is empty or consists only of whitespace.

        ValueError: If the document is not found or invalid values are provided for suggestionsViewMode.
        UserNotFoundError: If the `userId` is not found.
        
    """
    # Input Validation
    if not isinstance(documentId, str):
        raise TypeError("documentId must be a string.")
    if not documentId or not documentId.strip():
        raise ValueError("documentId cannot be empty or consist only of whitespace.")
        
    if suggestionsViewMode is not None and not isinstance(suggestionsViewMode, str):
        raise TypeError("suggestionsViewMode must be a string or None.")
    if not isinstance(includeTabsContent, bool):
        raise TypeError("includeTabsContent must be a boolean.")
    if not isinstance(userId, str):
        raise TypeError("userId must be a string.")
    if not userId or not userId.strip():
        raise ValueError("userId cannot be empty or consist only of whitespace.")
    if suggestionsViewMode is not None and suggestionsViewMode not in ["DEFAULT_FOR_CURRENT_ACCESS", "SUGGESTIONS_INLINE", "PREVIEW_SUGGESTIONS_ACCEPTED", "PREVIEW_WITHOUT_SUGGESTIONS"]:
        raise ValueError(f"Invalid value for suggestionsViewMode: {suggestionsViewMode}. Valid values are: DEFAULT_FOR_CURRENT_ACCESS, SUGGESTIONS_INLINE, PREVIEW_SUGGESTIONS_ACCEPTED, PREVIEW_WITHOUT_SUGGESTIONS.")

    # Check if user exists before performing read operation - this prevents implicit user creation
    if userId not in DB["users"]:
        raise UserNotFoundError(f"User with ID '{userId}' not found. Cannot perform read operation for non-existent user.")

    # The check below assumes _ensure_user has validated userId.
    # If userId itself was invalid and _ensure_user didn't raise,
    # DB["users"][userId] would raise a KeyError.
    if documentId not in DB["users"][userId]["files"]:
        raise ValueError(f"Document '{documentId}' not found")

    document = DB["users"][userId]["files"][documentId].copy()

    if suggestionsViewMode:
        document["suggestionsViewMode"] = suggestionsViewMode

    if includeTabsContent:
        document["includeTabsContent"] = includeTabsContent

    # Attach comments, replies, labels, accessproposals related to this doc
    # These accesses assume the structure of DB is consistent if userId and documentId are valid.
    document["comments"] = {
        cid: c
        for cid, c in DB["users"][userId]["comments"].items()
        if c["fileId"] == documentId
    }
    document["replies"] = {
        rid: r
        for rid, r in DB["users"][userId]["replies"].items()
        if r["fileId"] == documentId
    }
    document["labels"] = {
        lid: l
        for lid, l in DB["users"][userId]["labels"].items()
        if l["fileId"] == documentId
    }
    document["accessproposals"] = {
        pid: p
        for pid, p in DB["users"][userId]["accessproposals"].items()
        if p["fileId"] == documentId
    }

    # Transform content structure to match API documentation
    # Convert from textRun format to documented {elementId, text} format
    if "content" in document and document["content"]:
        # Handle different content structures
        content_data = document["content"]
        
        # If content is wrapped in a 'data' field (from hydrated database)
        if isinstance(content_data, dict) and "data" in content_data:
            content_list = content_data["data"]
        else:
            # If content is directly a list
            content_list = content_data
        
        # Ensure content_list is a list
        if not isinstance(content_list, list):
            content_list = []
        
        transformed_content = []
        element_counter = 1
        for content_element in content_list:
            if isinstance(content_element, dict):
                if "textRun" in content_element and "content" in content_element["textRun"]:
                    transformed_element = {
                        "elementId": f"p{element_counter}",
                        "text": content_element["textRun"]["content"]
                    }
                    transformed_content.append(transformed_element)
                    element_counter += 1
                elif "text" in content_element:
                    # Already in correct format, just ensure elementId exists
                    transformed_element = {
                        "elementId": content_element.get("elementId", f"p{element_counter}"),
                        "text": content_element["text"]
                    }
                    transformed_content.append(transformed_element)
                    element_counter += 1
                else:
                    # Other content types (tables, etc.) - preserve as-is but ensure elementId
                    if "elementId" not in content_element:
                        content_element["elementId"] = f"p{element_counter}"
                        element_counter += 1
                    transformed_content.append(content_element)
            else:
                # Skip non-dictionary elements
                continue
        document["content"] = transformed_content

    return document


@tool_spec(
    spec={
        'name': 'create_document',
        'description': 'Create a new document.',
        'parameters': {
            'type': 'object',
            'properties': {
                'title': {
                    'type': 'string',
                    'description': 'The title of the document. Defaults to "Untitled Document".'
                },
                'userId': {
                    'type': 'string',
                    'description': """ The ID of the user. Defaults to "me".
                    Must be a non-empty string. """
                }
            },
            'required': []
        }
    }
)
def create(
    title: str = "Untitled Document", userId: str = "me"
) -> Tuple[Dict[str, Union[str, bool, List[Union[str, Dict[str, str]]]]], int]:
    """Create a new document.

    Args:
        title (str): The title of the document. Defaults to "Untitled Document".
        userId (str): The ID of the user. Defaults to "me".
            Must be a non-empty string.

    Returns:
        Tuple[Dict[str, Union[str, bool, List[Union[str, Dict[str, str]]]]], int]: A tuple containing:
            - document (Dict[str, Union[str, bool, List[Union[str, Dict[str, str]]]]): The created document data with the following structure:
                - id (str): Unique document identifier (UUID format)
                - driveId (str): Drive identifier (empty string for new documents)
                - name (str): Document title
                - mimeType (str): Document MIME type ("application/vnd.google-apps.document")
                - createdTime (str): Creation timestamp in ISO format
                - modifiedTime (str): Last modification timestamp in ISO format
                - parents (List[str]): List of parent folder IDs
                - owners (List[str]): List of owner email addresses
                - suggestionsViewMode (str): Suggestions viewing mode ("DEFAULT")
                - includeTabsContent (bool): Whether to include tabs content (False)
                - content (List[Dict]): Document content elements (empty for new documents)
                - tabs (List[Dict]): Document tabs (empty for new documents)
                - permissions (List[Dict]): Access permissions with structure:
                    - role (str): Permission role (e.g., "owner")
                    - type (str): Permission type (e.g., "user")
                    - emailAddress (str): User's email address
                - trashed (bool): Whether document is in trash (False)
                - starred (bool): Whether document is starred (False)
                - size (str): Document size in bytes (string representation of integer)
            - status_code (int): HTTP status code (200 for success)

    Raises:
        TypeError: If 'title' or 'userId' is not a string.
        KeyError: If the specified `userId` does not exist in the database or
                  if expected data structures for the user are missing
                  (this error is propagated from internal operations).
        ValueError: If the specified `userId` is empty or only whitespace.

    """
    # --- Input Validation ---
    if not isinstance(title, str):
        raise TypeError(f"Argument 'title' must be a string, got {type(title).__name__}.")
    if not isinstance(userId, str):
        raise TypeError(f"Argument 'userId' must be a string, got {type(userId).__name__}.")
    
    # Value validation
    if not userId.strip():
        raise ValueError("Argument 'userId' cannot be empty or only whitespace.")
    # --- End of Input Validation ---

    # Check if user exists before creating document - this prevents implicit user creation
    if userId not in DB["users"]:
        raise KeyError(f"User with ID '{userId}' not found. Cannot create document for non-existent user.")

    documentId = str(uuid.uuid4())
    # The following DB access can raise KeyError if userId is not in DB or structure is unexpected
    user_data = DB["users"][userId]
    user_email = user_data["about"]["user"]["emailAddress"]

    # Get current timestamp in ISO format
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    document = {
        "id": documentId,
        "driveId": "",
        "name": title,
        "mimeType": "application/vnd.google-apps.document",
        "createdTime": current_time,
        "modifiedTime": current_time,
        "parents": [],
        "owners": [user_email],
        "suggestionsViewMode": "DEFAULT",
        "includeTabsContent": False,
        "content": [],
        "tabs": [],
        "permissions": [{"role": "owner", "type": "user", "emailAddress": user_email}],
        "trashed": False,
        "starred": False,
        "size": '0',
    }

    DB["users"][userId]["files"][documentId] = document # This access can also raise KeyError
    _next_counter("file", userId) # This call is assumed to exist

    return document, 200


@tool_spec(
    spec={
        'name': 'batch_update_document',
        'description': 'Apply batch updates to a document.',
        'parameters': {
            'type': 'object',
            'properties': {
                'documentId': {
                    'type': 'string',
                    'description': 'The ID of the document to update.'
                },
                'requests': {
                    'type': 'array',
                    'description': """ A list of update requests to apply. Each dictionary
                    in the list must be one of the specified request types. Each request
                    dictionary typically has a single key identifying the type of request
                    (e.g., 'insertText', 'updateDocumentStyle'), and its value is a dictionary containing the
                    parameters for that request. Note: Request names like "UpdateDocumentStyleRequest" 
                    are just type names, not keys to be used. The supported request types and their
                    structures are: """,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'InsertTextRequest': {
                                'type': 'object',
                                'description': "Corresponds to a dictionary with an 'insertText' key.",
                                'properties': {
                                    'insertText': {
                                        'type': 'object',
                                        'description': 'Inserts text into the document.',
                                        'properties': {
                                            'text': {
                                                'type': 'string',
                                                'description': 'The text to insert.'
                                            },
                                            'location': {
                                                'type': 'object',
                                                'description': 'Specifies where to insert the text.',
                                                'properties': {
                                                    'index': {
                                                        'type': 'integer',
                                                        'description': """ The zero-based index in the document's content
                                                                                    where the text will be inserted. """
                                                    }
                                                },
                                                'required': [
                                                    'index'
                                                ]
                                            }
                                        },
                                        'required': [
                                            'text'
                                        ]
                                    }
                                },
                                'required': []
                            },
                            'UpdateDocumentStyleRequest': {
                                'type': 'object',
                                'description': """ Corresponds to a dictionary with an
                                   'updateDocumentStyle' key. """,
                                'properties': {
                                    'updateDocumentStyle': {
                                        'type': 'object',
                                        'description': "Updates the document's style.",
                                        'properties': {
                                            'documentStyle': {
                                                'type': 'object',
                                                'description': """ The new document style to apply.
                                                             DocumentStyle represents the style of the document with the following structure: """,
                                                'properties': {
                                                    'background': {
                                                        'type': 'object',
                                                        'description': """ The background of the document. Documents cannot have a transparent background color.
                                                                         Background represents the background of a document with the following structure: """,
                                                        'properties': {
                                                            'color': {
                                                                'type': 'object',
                                                                'description': """ The background color.
                                                                                     Color represents a solid color with the following structure: """,
                                                                'properties': {
                                                                    'rgbColor': {
                                                                        'type': 'object',
                                                                        'description': """ The RGB color value.
                                                                                                 RgbColor represents an RGB color with the following structure: """,
                                                                        'properties': {
                                                                            'red': {
                                                                                'type': 'number',
                                                                                'description': 'The red component of the color, from 0.0 to 1.0.'
                                                                            },
                                                                            'green': {
                                                                                'type': 'number',
                                                                                'description': 'The green component of the color, from 0.0 to 1.0.'
                                                                            },
                                                                            'blue': {
                                                                                'type': 'number',
                                                                                'description': 'The blue component of the color, from 0.0 to 1.0.'
                                                                            }
                                                                        },
                                                                        'required': [
                                                                            'red',
                                                                            'green',
                                                                            'blue'
                                                                        ]
                                                                    }
                                                                },
                                                                'required': []
                                                            }
                                                        },
                                                        'required': []
                                                    },
                                                    'defaultHeaderId': {
                                                        'type': 'string',
                                                        'description': "The ID of the default header. If not set, there's no default header. This property is read-only."
                                                    },
                                                    'defaultFooterId': {
                                                        'type': 'string',
                                                        'description': "The ID of the default footer. If not set, there's no default footer. This property is read-only."
                                                    },
                                                    'evenPageHeaderId': {
                                                        'type': 'string',
                                                        'description': "The ID of the header used only for even pages. The value of useEvenPageHeaderFooter determines whether to use the defaultHeaderId or this value for the header on even pages. If not set, there's no even page header. This property is read-only."
                                                    },
                                                    'evenPageFooterId': {
                                                        'type': 'string',
                                                        'description': "The ID of the footer used only for even pages. The value of useEvenPageHeaderFooter determines whether to use the defaultFooterId or this value for the footer on even pages. If not set, there's no even page footer. This property is read-only."
                                                    },
                                                    'firstPageHeaderId': {
                                                        'type': 'string',
                                                        'description': "The ID of the header used only for the first page. If not set then a unique header for the first page does not exist. The value of useFirstPageHeaderFooter determines whether to use the defaultHeaderId or this value for the header on the first page. If not set, there's no first page header. This property is read-only."
                                                    },
                                                    'firstPageFooterId': {
                                                        'type': 'string',
                                                        'description': "The ID of the footer used only for the first page. If not set then a unique footer for the first page does not exist. The value of useFirstPageHeaderFooter determines whether to use the defaultFooterId or this value for the footer on the first page. If not set, there's no first page footer. This property is read-only."
                                                    },
                                                    'useFirstPageHeaderFooter': {
                                                        'type': 'boolean',
                                                        'description': 'Indicates whether to use the first page header / footer IDs for the first page.'
                                                    },
                                                    'useEvenPageHeaderFooter': {
                                                        'type': 'boolean',
                                                        'description': 'Indicates whether to use the even page header / footer IDs for the even pages.'
                                                    },
                                                    'pageNumberStart': {
                                                        'type': 'integer',
                                                        'description': 'The page number from which to start counting the number of pages.'
                                                    },
                                                    'marginTop': {
                                                        'type': 'object',
                                                        'description': """ The top page margin. Updating the top page margin on the document style clears the top page margin on all section styles.
                                                                         It has the following structure: """,
                                                        'properties': {
                                                            'magnitude': {
                                                                'type': 'number',
                                                                'description': 'The magnitude.'
                                                            },
                                                            'unit': {
                                                                'type': 'string',
                                                                'description': """ The units for magnitude. Possible values:
                                                                                     - "UNIT_UNSPECIFIED": The units are unknown.
                                                                                    - "PT": A point, 1/72 of an inch. """
                                                            }
                                                        },
                                                        'required': []
                                                    },
                                                    'marginBottom': {
                                                        'type': 'object',
                                                        'description': """ The bottom page margin. Updating the bottom page margin on the document style clears the bottom page margin on all section styles.
                                                                         It has the following structure: """,
                                                        'properties': {
                                                            'magnitude': {
                                                                'type': 'number',
                                                                'description': 'The magnitude.'
                                                            },
                                                            'unit': {
                                                                'type': 'string',
                                                                'description': """ The units for magnitude. Possible values:
                                                                                     - "UNIT_UNSPECIFIED": The units are unknown.
                                                                                    - "PT": A point, 1/72 of an inch. """
                                                            }
                                                        },
                                                        'required': []
                                                    },
                                                    'marginRight': {
                                                        'type': 'object',
                                                        'description': """ The right page margin. Updating the right page margin on the document style clears the right page margin on all section styles. It may also cause columns to resize in all sections.
                                                                         It has the following structure: """,
                                                        'properties': {
                                                            'magnitude': {
                                                                'type': 'number',
                                                                'description': 'The magnitude.'
                                                            },
                                                            'unit': {
                                                                'type': 'string',
                                                                'description': """ The units for magnitude. Possible values:
                                                                                     - "UNIT_UNSPECIFIED": The units are unknown.
                                                                                    - "PT": A point, 1/72 of an inch. """
                                                            }
                                                        },
                                                        'required': []
                                                    },
                                                    'marginLeft': {
                                                        'type': 'object',
                                                        'description': """ The left page margin. Updating the left page margin on the document style clears the left page margin on all section styles. It may also cause columns to resize in all sections.
                                                                         It has the following structure: """,
                                                        'properties': {
                                                            'magnitude': {
                                                                'type': 'number',
                                                                'description': 'The magnitude.'
                                                            },
                                                            'unit': {
                                                                'type': 'string',
                                                                'description': """ The units for magnitude. Possible values:
                                                                                     - "UNIT_UNSPECIFIED": The units are unknown.
                                                                                    - "PT": A point, 1/72 of an inch. """
                                                            }
                                                        },
                                                        'required': []
                                                    },
                                                    'pageSize': {
                                                        'type': 'object',
                                                        'description': 'The size of a page in the document. Must contain "height" and "width" keys.',
                                                        'properties': {
                                                            'height': {
                                                                'type': 'object',
                                                                'description': 'The height of the page.',
                                                                'properties': {
                                                                    'magnitude': {
                                                                        'type': 'number',
                                                                        'description': 'The magnitude.'
                                                                    },
                                                                    'unit': {
                                                                        'type': 'string',
                                                                        'description': 'The units for magnitude. Possible values: "UNIT_UNSPECIFIED", "PT" (point, 1/72 of an inch).'
                                                                    }
                                                                },
                                                                'required': []
                                                            },
                                                            'width': {
                                                                'type': 'object',
                                                                'description': 'The width of the page.',
                                                                'properties': {
                                                                    'magnitude': {
                                                                        'type': 'number',
                                                                        'description': 'The magnitude.'
                                                                    },
                                                                    'unit': {
                                                                        'type': 'string',
                                                                        'description': 'The units for magnitude. Possible values: "UNIT_UNSPECIFIED", "PT" (point, 1/72 of an inch).'
                                                                    }
                                                                },
                                                                'required': []
                                                            }
                                                        },
                                                        'required': ['height', 'width']
                                                    },
                                                    'marginHeader': {
                                                        'type': 'object',
                                                        'description': """ The amount of space between the top of the page and the contents of the header.
                                                                         It has the following structure: """,
                                                        'properties': {
                                                            'magnitude': {
                                                                'type': 'number',
                                                                'description': 'The magnitude.'
                                                            },
                                                            'unit': {
                                                                'type': 'string',
                                                                'description': """ The units for magnitude. Possible values:
                                                                                     - "UNIT_UNSPECIFIED": The units are unknown.
                                                                                    - "PT": A point, 1/72 of an inch. """
                                                            }
                                                        },
                                                        'required': []
                                                    },
                                                    'marginFooter': {
                                                        'type': 'object',
                                                        'description': """ The amount of space between the bottom of the page and the contents of the footer.
                                                                         It has the following structure: """,
                                                        'properties': {
                                                            'magnitude': {
                                                                'type': 'number',
                                                                'description': 'The magnitude.'
                                                            },
                                                            'unit': {
                                                                'type': 'string',
                                                                'description': """ The units for magnitude. Possible values:
                                                                                     - "UNIT_UNSPECIFIED": The units are unknown.
                                                                                    - "PT": A point, 1/72 of an inch. """
                                                            }
                                                        },
                                                        'required': []
                                                    },
                                                    'useCustomHeaderFooterMargins': {
                                                        'type': 'boolean',
                                                        'description': 'Indicates whether DocumentStyle marginHeader, SectionStyle marginHeader and DocumentStyle marginFooter, SectionStyle marginFooter are respected. When false, the default values in the Docs editor for header and footer margin is used. This property is read-only.'
                                                    },
                                                    'flipPageOrientation': {
                                                        'type': 'boolean',
                                                        'description': 'Optional. Indicates whether to flip the dimensions of the pageSize, which allows changing the page orientation between portrait and landscape.'
                                                    }
                                                },
                                                'required': []
                                            }
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            },
                            'DeleteContentRangeRequest': {
                                'type': 'object',
                                'description': """ Corresponds to a dictionary with a
                                   'deleteContentRange' key. """,
                                'properties': {
                                    'deleteContentRange': {
                                        'type': 'object',
                                        'description': 'Deletes content within a specified range in the document.',
                                        'properties': {
                                            'range': {
                                                'type': 'object',
                                                'description': 'The range of content to delete.',
                                                'properties': {
                                                    'startIndex': {
                                                        'type': 'integer',
                                                        'description': 'The zero-based start index of the range to delete.'
                                                    },
                                                    'endIndex': {
                                                        'type': 'integer',
                                                        'description': 'The zero-based end index of the range to delete (exclusive).'
                                                    }
                                                },
                                                'required': ['startIndex', 'endIndex']
                                            }
                                        },
                                        'required': ['range']
                                    }
                                },
                                'required': []
                            },
                            'ReplaceAllTextRequest': {
                                'type': 'object',
                                'description': """ Corresponds to a dictionary with a
                                   'replaceAllText' key. """,
                                'properties': {
                                    'replaceAllText': {
                                        'type': 'object',
                                        'description': 'Replaces all instances of specified text in the document.',
                                        'properties': {
                                            'containsText': {
                                                'type': 'object',
                                                'description': 'Criteria for matching text to replace.',
                                                'properties': {
                                                    'text': {
                                                        'type': 'string',
                                                        'description': 'The text to search for and replace.'
                                                    },
                                                    'matchCase': {
                                                        'type': 'boolean',
                                                        'description': 'Whether to match case. Defaults to False.'
                                                    }
                                                },
                                                'required': ['text']
                                            },
                                            'replaceText': {
                                                'type': 'string',
                                                'description': 'The text that will replace the matched text.'
                                            }
                                        },
                                        'required': ['containsText', 'replaceText']
                                    }
                                },
                                'required': []
                            },
                            'InsertTableRequest': {
                                'type': 'object',
                                'description': """ Corresponds to a dictionary with an
                                   'insertTable' key. """,
                                'properties': {
                                    'insertTable': {
                                        'type': 'object',
                                        'description': 'Inserts a table into the document.',
                                        'properties': {
                                            'rows': {
                                                'type': 'integer',
                                                'description': 'The number of rows in the table. Must be between 1 and 20.'
                                            },
                                            'columns': {
                                                'type': 'integer',
                                                'description': 'The number of columns in the table. Must be between 1 and 20.'
                                            },
                                            'location': {
                                                'type': 'object',
                                                'description': 'Specifies where to insert the table by index.',
                                                'properties': {
                                                    'index': {
                                                        'type': 'integer',
                                                        'description': """ The zero-based index in the document's content
                                                                                    where the table will be inserted. """
                                                    }
                                                },
                                                'required': [
                                                    'index'
                                                ]
                                            },
                                            'endOfSegmentLocation': {
                                                'type': 'object',
                                                'description': 'Specifies where to insert the table at the end of a segment.',
                                                'properties': {
                                                    'segmentId': {
                                                        'type': 'string',
                                                        'description': 'The ID of the segment where the table will be inserted at the end. Empty string ("") indicates document body.'
                                                    }
                                                },
                                                'required': [
                                                    'segmentId'
                                                ]
                                            }
                                        },
                                        'required': [
                                            'rows',
                                            'columns'
                                        ]
                                    }
                                },
                                'required': []
                            }
                        },
                        'required': []
                    }
                },
                'userId': {
                    'type': 'string',
                    'description': 'The ID of the user. Defaults to "me".'
                }
            },
            'required': [
                'documentId',
                'requests'
            ]
        }
    }
)
def batchUpdate(
    documentId: str, requests: List[Dict[str, Any]], userId: Optional[str] = "me"
) -> Tuple[Dict[str, Union[str, List[Dict[str, Dict[str, Union[Dict, int]]]]]], int]:
    """Apply batch updates to a document.

    Args:
        documentId (str): The ID of the document to update.
        requests (List[Dict[str, Any]]): A list of update requests to apply. Each dictionary
            in the list must be one of the specified request types. Each request
            dictionary typically has a single key identifying the type of request
            (e.g., 'insertText', 'updateDocumentStyle'), and its value is a dictionary containing the
            parameters for that request. Note: Request names like "UpdateDocumentStyleRequest" 
            are just type names, not keys to be used. The supported request types and their
            structures are:
            - InsertTextRequest (Optional[Dict[str, Any]]): Corresponds to a dictionary with an 'insertText' key.
                - 'insertText' (Optional[Dict[str, Any]]): Inserts text into the document.
                    - 'text' (str): The text to insert.
                    - 'location' (Optional[Dict[str, Any]]): Specifies where to insert the text.
                        - 'index' (int): The zero-based index in the document's content
                                       where the text will be inserted.
            - UpdateDocumentStyleRequest (Optional[Dict[str, Any]]): Corresponds to a dictionary with an
              'updateDocumentStyle' key.
                - 'updateDocumentStyle' (Optional[Dict[str, Any]]): Updates the document's style.
                    - 'documentStyle' (Optional[Dict[str, Any]]): The new document style to apply. 
                        DocumentStyle represents the style of the document with the following structure:
                        - 'background' (Optional[Dict[str, Any]]): The background of the document. Documents cannot have a transparent background color.
                            Background represents the background of a document with the following structure:
                            - 'color' (Optional[Dict[str, Any]]): The background color.
                                Color represents a solid color with the following structure:
                                
                                - 'rgbColor' (Optional[Dict[str, Any]]): The RGB color value.
                                    RgbColor represents an RGB color with the following structure:
                                    
                                    - 'red' (float): The red component of the color, from 0.0 to 1.0.
                                    - 'green' (float): The green component of the color, from 0.0 to 1.0.
                                    - 'blue' (float): The blue component of the color, from 0.0 to 1.0.
                        - 'defaultHeaderId' (Optional[str]): The ID of the default header. If not set, there's no default header. This property is read-only.
                        - 'defaultFooterId' (Optional[str]): The ID of the default footer. If not set, there's no default footer. This property is read-only.
                        - 'evenPageHeaderId' (Optional[str]): The ID of the header used only for even pages. The value of useEvenPageHeaderFooter determines whether to use the defaultHeaderId or this value for the header on even pages. If not set, there's no even page header. This property is read-only.
                        - 'evenPageFooterId' (Optional[str]): The ID of the footer used only for even pages. The value of useEvenPageHeaderFooter determines whether to use the defaultFooterId or this value for the footer on even pages. If not set, there's no even page footer. This property is read-only.
                        - 'firstPageHeaderId' (Optional[str]): The ID of the header used only for the first page. If not set then a unique header for the first page does not exist. The value of useFirstPageHeaderFooter determines whether to use the defaultHeaderId or this value for the header on the first page. If not set, there's no first page header. This property is read-only.
                        - 'firstPageFooterId' (Optional[str]): The ID of the footer used only for the first page. If not set then a unique footer for the first page does not exist. The value of useFirstPageHeaderFooter determines whether to use the defaultFooterId or this value for the footer on the first page. If not set, there's no first page footer. This property is read-only.
                        - 'useFirstPageHeaderFooter' (Optional[bool]): Indicates whether to use the first page header / footer IDs for the first page.
                        - 'useEvenPageHeaderFooter' (Optional[bool]): Indicates whether to use the even page header / footer IDs for the even pages.
                        -'pageNumberStart' (Optional[int]): The page number from which to start counting the number of pages.
                        - 'marginTop' (Optional[Dict[str, Any]]): The top page margin. Updating the top page margin on the document style clears the top page margin on all section styles.
                            It has the following structure:
                            - 'magnitude' (Optional[float]): The magnitude.
                            - 'unit' (Optional[str]): The units for magnitude. Possible values:
                                - "UNIT_UNSPECIFIED": The units are unknown.
                                - "PT": A point, 1/72 of an inch.
                        - 'marginBottom' (Optional[Dict[str, Any]]): The bottom page margin. Updating the bottom page margin on the document style clears the bottom page margin on all section styles.
                            It has the following structure:
                            - 'magnitude' (Optional[float]): The magnitude.
                            - 'unit' (Optional[str]): The units for magnitude. Possible values:
                                - "UNIT_UNSPECIFIED": The units are unknown.
                                - "PT": A point, 1/72 of an inch.
                        - 'marginRight' (Optional[Dict[str, Any]]): The right page margin. Updating the right page margin on the document style clears the right page margin on all section styles. It may also cause columns to resize in all sections.
                            It has the following structure:
                            - 'magnitude' (Optional[float]): The magnitude.
                            - 'unit' (Optional[str]): The units for magnitude. Possible values:
                                - "UNIT_UNSPECIFIED": The units are unknown.
                                - "PT": A point, 1/72 of an inch.
                        - 'marginLeft' (Optional[Dict[str, Any]]): The left page margin. Updating the left page margin on the document style clears the left page margin on all section styles. It may also cause columns to resize in all sections.
                            It has the following structure:
                            - 'magnitude' (Optional[float]): The magnitude.
                            - 'unit' (Optional[str]): The units for magnitude. Possible values:
                                - "UNIT_UNSPECIFIED": The units are unknown.
                                - "PT": A point, 1/72 of an inch.
                        - 'pageSize' (Optional[Dict[str, Any]]): The size of a page in the document.
                            It has the following structure:
                            - 'height' (Optional[Dict[str, Any]]): The height of the page.
                                - 'magnitude' (Optional[float]): The magnitude.
                                - 'unit' (Optional[str]): The units for magnitude. Possible values:
                                    - "UNIT_UNSPECIFIED": The units are unknown.
                                    - "PT": A point, 1/72 of an inch.
                            - 'width' (Optional[Dict[str, Any]]): The width of the page.
                                - 'magnitude' (Optional[float]): The magnitude.
                                - 'unit' (Optional[str]): The units for magnitude. Possible values:
                                    - "UNIT_UNSPECIFIED": The units are unknown.
                                    - "PT": A point, 1/72 of an inch.
                        - 'marginHeader' (Optional[Dict[str, Any]]): The amount of space between the top of the page and the contents of the header.
                            It has the following structure:
                            - 'magnitude' (Optional[float]): The magnitude.
                            - 'unit' (Optional[str]): The units for magnitude. Possible values:
                                - "UNIT_UNSPECIFIED": The units are unknown.
                                - "PT": A point, 1/72 of an inch.
                        - 'marginFooter' (Optional[Dict[str, Any]]): The amount of space between the bottom of the page and the contents of the footer.
                            It has the following structure:
                            - 'magnitude' (Optional[float]): The magnitude.
                            - 'unit' (Optional[str]): The units for magnitude. Possible values:
                                - "UNIT_UNSPECIFIED": The units are unknown.
                                - "PT": A point, 1/72 of an inch.
                        - 'useCustomHeaderFooterMargins' (Optional[bool]): Indicates whether DocumentStyle marginHeader, SectionStyle marginHeader and DocumentStyle marginFooter, SectionStyle marginFooter are respected. When false, the default values in the Docs editor for header and footer margin is used. This property is read-only.
                        - 'flipPageOrientation' (Optional[bool]): Optional. Indicates whether to flip the dimensions of the pageSize, which allows changing the page orientation between portrait and landscape.
            - DeleteContentRangeRequest (Optional[Dict[str, Any]]): Corresponds to a dictionary with a
              'deleteContentRange' key.
                - 'deleteContentRange' (Optional[Dict[str, Any]]): Deletes content within a specified range in the document.
                    - 'range' (Dict[str, Any]): The range of content to delete.
                        - 'startIndex' (int): The zero-based start index of the range to delete.
                        - 'endIndex' (int): The zero-based end index of the range to delete (exclusive).
            - ReplaceAllTextRequest (Optional[Dict[str, Any]]): Corresponds to a dictionary with a
              'replaceAllText' key.
                - 'replaceAllText' (Optional[Dict[str, Any]]): Replaces all instances of specified text in the document.
                    - 'containsText' (Dict[str, Any]): Criteria for matching text to replace.
                        - 'text' (str): The text to search for and replace.
                        - 'matchCase' (Optional[bool]): Whether to match case. Defaults to False.
                    - 'replaceText' (str): The text that will replace the matched text.
            - InsertTableRequest (Optional[Dict[str, Any]]): Corresponds to a dictionary with an
              'insertTable' key.
                - 'insertTable' (Optional[Dict[str, Any]]): Inserts a table into the document.
                    - 'rows' (int): The number of rows in the table. Must be between 1 and 20.
                    - 'columns' (int): The number of columns in the table. Must be between 1 and 20.
                    - 'location' (Optional[Dict[str, Any]]): Specifies where to insert the table by index.
                        - 'index' (int): The zero-based index in the document's content
                                       where the table will be inserted.
                    - 'endOfSegmentLocation' (Optional[Dict[str, Any]]): Specifies where to insert the table at the end of a segment.
                        - 'segmentId' (str): The ID of the segment where the table will be inserted at the end. Empty string ("") indicates document body.
                    Note: Either 'location' or 'endOfSegmentLocation' must be provided, but not both.
        userId (Optional[str]): The ID of the user. Defaults to "me".

    Returns:
        Tuple[Dict[str, Union[str, List[Dict[str, Dict[str, Union[Dict, int]]]]]], int]: A tuple containing:
            - Dict[str, Union[str, List[Dict[str, Dict[str, Union[Dict, int]]]]]]: The batch update response with the following structure:
                - documentId (str): The ID of the document that was updated
                - replies (List[Dict[str, Dict[str, Union[Dict, int]]]]): List of reply objects for each request in the batch, where each reply contains:
                    - For insertText requests: {"insertText": {}}
                    - For updateDocumentStyle requests: {"updateDocumentStyle": {}}
                    - For deleteContentRange requests: {"deleteContentRange": {}}
                    - For replaceAllText requests: {"replaceAllText": {"occurrencesChanged": int}}
                    - For insertTable requests: {"insertTable": {}}
            - int: HTTP status code (200 for success)

    Raises:
        TypeError: If `documentId` or `userId` are not strings or `requests` is not a list
            or any item in `requests` is not a dictionary with a valid request type.
        pydantic.ValidationError: If any item in `requests` does not conform to the defined
            structures (e.g., InsertTextRequestModel, UpdateDocumentStyleRequestModel, 
            DeleteContentRangeRequestModel, ReplaceAllTextRequestModel, InsertTableRequestModel), such as incorrect 
            field types, missing required fields, or including extra fields.
        ValueError: If range indices in deleteContentRange are invalid (negative, start > end, 
            or start beyond content length).
        ValueError: If table dimensions in insertTable are invalid (rows or columns not between 1 and 20).
        ValueError: If neither 'location' nor 'endOfSegmentLocation' is provided in insertTable.
        ValueError: If both 'location' and 'endOfSegmentLocation' are provided in insertTable.
        FileNotFoundError: If the document is not found.

    """
    # --- BEGIN INPUT VALIDATION ---
    if not isinstance(documentId, str):
        raise TypeError("documentId must be a string.")
    if not isinstance(userId, str):
        raise TypeError("userId must be a string.")
    if not isinstance(requests, List):
        raise TypeError("requests must be a list.")

    # Validate all requests and store validated models for type-safe processing
    validated_requests = []
    for request in requests:
        if not isinstance(request, dict):
            raise TypeError("request must be a dictionary.")
        if not any(key in request for key in ["insertText", "updateDocumentStyle", "deleteContentRange", "replaceAllText", "insertTable"]):
            raise TypeError("Unsupported request type.")
        
        # Validate and convert types using Pydantic models
        if "insertText" in request:
            validated_request = InsertTextRequestModel.model_validate(request)
        elif "updateDocumentStyle" in request:
            validated_request = UpdateDocumentStyleRequestModel.model_validate(request)
        elif "deleteContentRange" in request:
            validated_request = DeleteContentRangeRequestModel.model_validate(request)
        elif "replaceAllText" in request:
            validated_request = ReplaceAllTextRequestModel.model_validate(request)
        elif "insertTable" in request:
            validated_request = InsertTableRequestModel.model_validate(request)
        
        validated_requests.append(validated_request)

    # --- END INPUT VALIDATION ---

    if documentId not in DB["users"][userId]["files"]:
        raise FileNotFoundError(f"Document with ID '{documentId}' not found.")

    document = DB["users"][userId]["files"][documentId]
    replies = []

    # Process validated requests with converted types
    for validated_request in validated_requests:
        if hasattr(validated_request, 'insertText'):
            insert_text = validated_request.insertText
            text = insert_text.text
            location = insert_text.location.index  # Already converted to int by Pydantic

            if "content" not in document or document["content"] is None:
                document["content"] = []

            # Generate elementId for the new content element
            element_counter = len(document["content"]) + 1
            element_id = f"p{element_counter}"
            
            # Insert content in the consistent {elementId, text} format
            document["content"].insert(location, {"elementId": element_id, "text": text})

            replies.append({"insertText": {}})

        elif hasattr(validated_request, 'updateDocumentStyle'):
            update_style = validated_request.updateDocumentStyle
            document["documentStyle"] = update_style.documentStyle
            replies.append({"updateDocumentStyle": {}})

        elif hasattr(validated_request, 'deleteContentRange'):
            delete_range = validated_request.deleteContentRange
            range_obj = delete_range.range
            start_index = range_obj.startIndex  # Already converted to int by Pydantic
            end_index = range_obj.endIndex  # Already converted to int by Pydantic

            if "content" not in document or document["content"] is None:
                document["content"] = []

            # Validate range indices
            content_length = len(document["content"])
            if start_index < 0 or end_index < 0:
                raise ValueError("Range indices must be non-negative.")
            if start_index > end_index:
                raise ValueError("startIndex must be less than or equal to endIndex.")
            if start_index > content_length:
                raise ValueError("startIndex is beyond document content length.")
            
            # Clamp end_index to content length if it exceeds
            end_index = min(end_index, content_length)
            
            # Delete the specified range
            if start_index < content_length:
                del document["content"][start_index:end_index]

            replies.append({"deleteContentRange": {}})

        elif hasattr(validated_request, 'replaceAllText'):
            replace_all = validated_request.replaceAllText
            contains_text = replace_all.containsText
            search_text = contains_text.text
            match_case = contains_text.matchCase if hasattr(contains_text, 'matchCase') else False
            replace_text = replace_all.replaceText

            if "content" not in document or document["content"] is None:
                document["content"] = []

            # Perform text replacement in all content elements
            replacements_made = 0
            for content_item in document["content"]:
                # Handle both old textRun format and new consistent format
                if "textRun" in content_item and "content" in content_item["textRun"]:
                    # Legacy textRun format - always convert to consistent format
                    original_text = content_item["textRun"]["content"]
                    element_id = content_item.get("elementId", f"p{len(document['content'])}")
                    
                    # Always convert to consistent format
                    new_text = original_text
                    
                    if match_case:
                        # Case-sensitive replacement
                        if search_text in original_text:
                            new_text = original_text.replace(search_text, replace_text)
                            replacements_made += original_text.count(search_text)
                    else:
                        # Case-insensitive replacement
                        import re
                        pattern = re.compile(re.escape(search_text), re.IGNORECASE)
                        matches = pattern.findall(original_text)
                        if matches:
                            new_text = pattern.sub(replace_text, original_text)
                            replacements_made += len(matches)
                    
                    # Always convert to consistent format regardless of matches
                    content_item["text"] = new_text
                    content_item["elementId"] = element_id
                    del content_item["textRun"]  # Remove old format
                elif "text" in content_item:
                    # Consistent format - direct replacement
                    original_text = content_item["text"]
                    
                    if match_case:
                        # Case-sensitive replacement
                        if search_text in original_text:
                            new_text = original_text.replace(search_text, replace_text)
                            content_item["text"] = new_text
                            replacements_made += original_text.count(search_text)
                    else:
                        # Case-insensitive replacement
                        import re
                        pattern = re.compile(re.escape(search_text), re.IGNORECASE)
                        matches = pattern.findall(original_text)
                        if matches:
                            new_text = pattern.sub(replace_text, original_text)
                            content_item["text"] = new_text
                            replacements_made += len(matches)

            replies.append({"replaceAllText": {"occurrencesChanged": replacements_made}})

        elif hasattr(validated_request, 'insertTable'):
            insert_table = validated_request.insertTable
            rows = insert_table.rows  # Already converted to int by Pydantic
            columns = insert_table.columns  # Already converted to int by Pydantic
            
            # Validate table dimensions
            if rows < 1 or rows > 20:
                raise ValueError("rows must be between 1 and 20.")
            if columns < 1 or columns > 20:
                raise ValueError("columns must be between 1 and 20.")
            
            # Validate location specification
            location = insert_table.location if hasattr(insert_table, 'location') else None
            end_of_segment_location = insert_table.endOfSegmentLocation if hasattr(insert_table, 'endOfSegmentLocation') else None
            
            if not location and not end_of_segment_location:
                raise ValueError("Either 'location' or 'endOfSegmentLocation' must be provided.")
            if location and end_of_segment_location:
                raise ValueError("Cannot specify both 'location' and 'endOfSegmentLocation'.")

            if "content" not in document or document["content"] is None:
                document["content"] = []

            # Generate elementIds for new content elements
            current_content_length = len(document["content"])
            newline_element_id = f"p{current_content_length + 1}"
            table_element_id = f"p{current_content_length + 2}"

            # Create table structure (official API automatically inserts newline before table)
            newline_content = {"elementId": newline_element_id, "text": "\n"}
            table_content = {
                "elementId": table_element_id,
                "table": {
                    "rows": rows,
                    "columns": columns,
                    "tableRows": []
                }
            }

            # Create table rows
            for row_idx in range(rows):
                table_row = {
                    "tableCells": []
                }
                for col_idx in range(columns):
                    table_cell = {
                        "content": [{"elementId": f"cell_{row_idx}_{col_idx}", "text": ""}]
                    }
                    table_row["tableCells"].append(table_cell)
                table_content["table"]["tableRows"].append(table_row)

            # Determine insertion location
            if location:
                # Insert at specific index (newline + table)
                insert_index = location.index  # Already converted to int by Pydantic
                document["content"].insert(insert_index, newline_content)
                document["content"].insert(insert_index + 1, table_content)
            else:
                # Insert at end of segment (newline + table)
                document["content"].append(newline_content)
                document["content"].append(table_content)
            
            replies.append({"insertTable": {}})

    DB["users"][userId]["files"][documentId] = document
    return {"documentId": documentId, "replies": replies}, 200
