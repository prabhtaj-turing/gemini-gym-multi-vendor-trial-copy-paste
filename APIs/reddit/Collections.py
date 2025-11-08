from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine.db import DB
from typing import Dict, Any, List

"""
Simulation of /collections endpoints.
Manages collections of posts within subreddits.
"""

@tool_spec(
    spec={
        'name': 'add_post_to_collection',
        'description': 'Adds a post to an existing collection.',
        'parameters': {
            'type': 'object',
            'properties': {
                'collection_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the collection.'
                },
                'link_fullname': {
                    'type': 'string',
                    'description': 'The fullname of the post to add.'
                }
            },
            'required': [
                'collection_id',
                'link_fullname'
            ]
        }
    }
)
def post_api_v1_collections_add_post_to_collection(collection_id: str, link_fullname: str) -> Dict[str, Any]:
    """
    Adds a post to an existing collection.

    Args:
        collection_id (str): The unique identifier of the collection.
        link_fullname (str): The fullname of the post to add.

    Returns:
        Dict[str, Any]:
        - If the collection does not exist, returns a dictionary with the key "error" and the value "Collection does not exist".
        - On successful addition, returns a dictionary with the following keys:
            - status (str): The status of the operation ("success")
            - collection_id (str): The ID of the updated collection
            - added_link (str): The fullname of the added post
    """
    if collection_id not in DB["collections"]:
        return {"error": "Collection does not exist"}
    coll = DB["collections"][collection_id]
    coll.setdefault("links", [])
    coll["links"].append(link_fullname)
    return {"status": "success", "collection_id": collection_id, "added_link": link_fullname}

@tool_spec(
    spec={
        'name': 'get_collection_info',
        'description': 'Retrieves information about a specific collection.',
        'parameters': {
            'type': 'object',
            'properties': {
                'collection_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the collection.'
                }
            },
            'required': [
                'collection_id'
            ]
        }
    }
)
def get_api_v1_collections_collection(collection_id: str) -> Dict[str, Any]:
    """
    Retrieves information about a specific collection.

    Args:
        collection_id (str): The unique identifier of the collection.

    Returns:
        Dict[str, Any]:
        - If the collection does not exist, returns a dictionary with the key "error" and the value "Collection not found".
        - On successful retrieval, returns a dictionary containing the following keys:
            - title (str): The title of the collection
            - sr_fullname (str): The fullname of the subreddit the collection belongs to.
            - links (List[str]): List of post fullnames in the collection.
            - description (str): Optional description of the collection.
            - num_followers (int): The number of followers of the collection.
            - display_layout (str): The display layout of the collection (e.g., "TIMELINE").
            - is_following (bool): Whether the user is following the collection.
    """
    return DB["collections"].get(collection_id, {"error": "Collection not found"})

@tool_spec(
    spec={
        'name': 'create_collection',
        'description': 'Creates a new collection in a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'title': {
                    'type': 'string',
                    'description': 'The title of the new collection.'
                },
                'sr_fullname': {
                    'type': 'string',
                    'description': 'The fullname of the subreddit.'
                }
            },
            'required': [
                'title',
                'sr_fullname'
            ]
        }
    }
)
def post_api_v1_collections_create_collection(title: str, sr_fullname: str) -> Dict[str, Any]:
    """
    Creates a new collection in a subreddit.

    Args:
        title (str): The title of the new collection.
        sr_fullname (str): The fullname of the subreddit.

    Returns:
        Dict[str, Any]: Returns a dictionary with the following keys:
            - status (str): The status of the creation ("collection_created")
            - collection_id (str): The ID of the newly created collection
    """
    new_id = f"col_{len(DB.get('collections', {}))+1}" # Use .get for safety
    DB.setdefault("collections", {})[new_id] = {
        "title": title,
        "sr_fullname": sr_fullname,
        "links": [],
        "description": "",
        "display_layout": "TIMELINE",
        "num_followers": 0,
        "is_following": False
    }
    return {"status": "collection_created", "collection_id": new_id}

@tool_spec(
    spec={
        'name': 'delete_collection',
        'description': 'Deletes an existing collection.',
        'parameters': {
            'type': 'object',
            'properties': {
                'collection_id': {
                    'type': 'string',
                    'description': 'The identifier of the collection to delete.'
                }
            },
            'required': [
                'collection_id'
            ]
        }
    }
)
def post_api_v1_collections_delete_collection(collection_id: str) -> Dict[str, Any]:
    """
    Deletes an existing collection.

    Args:
        collection_id (str): The identifier of the collection to delete.

    Returns:
        Dict[str, Any]:
        - If the collection does not exist, returns a dictionary with the key "error" and the value "Collection not found".
        - On successful deletion, returns a dictionary with the following keys:
            - status (str): The status of the deletion ("collection_deleted")
            - collection_id (str): The ID of the deleted collection
    """
    if collection_id in DB.get("collections", {}):
        del DB["collections"][collection_id]
        return {"status": "collection_deleted", "collection_id": collection_id}
    return {"error": "Collection not found"}

@tool_spec(
    spec={
        'name': 'remove_post_from_collection',
        'description': 'Removes a post from a collection.',
        'parameters': {
            'type': 'object',
            'properties': {
                'link_fullname': {
                    'type': 'string',
                    'description': 'The fullname of the post to remove.'
                },
                'collection_id': {
                    'type': 'string',
                    'description': 'The identifier of the collection.'
                }
            },
            'required': [
                'link_fullname',
                'collection_id'
            ]
        }
    }
)
def post_api_v1_collections_remove_post_in_collection(link_fullname: str, collection_id: str) -> Dict[str, Any]:
    """
    Removes a post from a collection.

    Args:
        link_fullname (str): The fullname of the post to remove.
        collection_id (str): The identifier of the collection.

    Returns:
        Dict[str, Any]:
        - If the collection does not exist, returns a dictionary with the key "error" and the value "No such collection".
        - If the post is not found in the collection, returns a dictionary with the key "error" and the value "Link not found in collection".
        - On successful removal, returns a dictionary with the following keys:
            - status (str): The status of the removal ("success")
            - removed_link (str): The fullname of the removed post
    """
    coll = DB.get("collections", {}).get(collection_id)
    if not coll:
        return {"error": "No such collection"}
    if link_fullname in coll.get("links", []):
        coll["links"].remove(link_fullname)
        return {"status": "success", "removed_link": link_fullname}
    return {"error": "Link not found in collection"}

@tool_spec(
    spec={
        'name': 'reorder_collection_posts',
        'description': 'Reorders the posts in a collection.',
        'parameters': {
            'type': 'object',
            'properties': {
                'collection_id': {
                    'type': 'string',
                    'description': 'The identifier of the collection.'
                },
                'link_ids': {
                    'type': 'array',
                    'description': 'The list of comma separated link_ids in the order to set them in.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'collection_id',
                'link_ids'
            ]
        }
    }
)
def post_api_v1_collections_reorder_collection(collection_id: str, link_ids: List[str]) -> Dict[str, Any]:
    """
    Reorders the posts in a collection.

    Args:
        collection_id (str): The identifier of the collection.
        link_ids (List[str]): The list of comma separated link_ids in the order to set them in.

    Returns:
        Dict[str, Any]:
        - If the collection does not exist, returns a dictionary with the key "error" and the value "No such collection".
        - On successful reordering, returns a dictionary with the following keys:
            - status (str): The status of the reordering ("success")
            - collection_id (str): The ID of the collection
            - new_order (List[str]): The new order of link IDs
    """
    coll = DB.get("collections", {}).get(collection_id)
    if not coll:
        return {"error": "No such collection"}
    coll["links"] = link_ids
    return {"status": "success", "collection_id": collection_id, "new_order": link_ids}

@tool_spec(
    spec={
        'name': 'get_subreddit_collections',
        'description': 'Retrieves collections for a specific subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'sr_fullname': {
                    'type': 'string',
                    'description': 'The fullname of the subreddit.'
                }
            },
            'required': [
                'sr_fullname'
            ]
        }
    }
)
def get_api_v1_collections_subreddit_collections(sr_fullname: str) -> List[Dict[str, Any]]:
    """
    Retrieves collections for a specific subreddit.

    Args:
        sr_fullname (str): The fullname of the subreddit.

    Returns:
        List[Dict[str, Any]]: A list of collections, where each collection is represented
                             as a dictionary containing the following keys:
            - title (str): The title of the collection
            - sr_fullname (str): The fullname of the subreddit the collection belongs to.
            - links (List[str]): List of post fullnames in the collection.
            - description (str): Optional description of the collection.
            - num_followers (int): The number of followers of the collection.
            - display_layout (str): The display layout of the collection (e.g., "TIMELINE").
            - is_following (bool): Whether the user is following the collection.
    """
    result = []
    for cid, cdata in DB.get("collections", {}).items():
        if cdata.get("sr_fullname") == sr_fullname: # Use .get for safety
            result.append({cid: cdata})
    return result

@tool_spec(
    spec={
        'name': 'update_collection_description',
        'description': 'Updates the description of a collection.',
        'parameters': {
            'type': 'object',
            'properties': {
                'collection_id': {
                    'type': 'string',
                    'description': 'The collection identifier.'
                },
                'description': {
                    'type': 'string',
                    'description': 'The new description text.'
                }
            },
            'required': [
                'collection_id',
                'description'
            ]
        }
    }
)
def post_api_v1_collections_update_collection_description(collection_id: str, description: str) -> Dict[str, Any]:
    """
    Updates the description of a collection.

    Args:
        collection_id (str): The collection identifier.
        description (str): The new description text.

    Returns:
        Dict[str, Any]:
        - If the collection does not exist, returns a dictionary with the key "error" and the value "No such collection".
        - On successful update, returns a dictionary with the following keys:
            - status (str): The status of the update ("success")
            - collection_id (str): the UUID of a collection.
            - new_description (str): The updated description, a string no longer than 500 characters.

    Raises:
        ValueError: If the description is longer than 500 characters.
    """
    if len(description) > 500:
        raise ValueError("Description cannot be longer than 500 characters")
    coll = DB.get("collections", {}).get(collection_id)
    if not coll:
        return {"error": "No such collection"}
    coll["description"] = description
    return {"status": "success", "collection_id": collection_id, "new_description": description}

@tool_spec(
    spec={
        'name': 'update_collection_display_layout',
        'description': 'Updates the display layout of a collection.',
        'parameters': {
            'type': 'object',
            'properties': {
                'collection_id': {
                    'type': 'string',
                    'description': 'The collection identifier.'
                },
                'display_layout': {
                    'type': 'string',
                    'description': 'The new layout style (e.g., GALLERY, TIMELINE).'
                }
            },
            'required': [
                'collection_id',
                'display_layout'
            ]
        }
    }
)
def post_api_v1_collections_update_collection_display_layout(collection_id: str, display_layout: str) -> Dict[str, Any]:
    """
    Updates the display layout of a collection.

    Args:
        collection_id (str): The collection identifier.
        display_layout (str): The new layout style (e.g., GALLERY, TIMELINE).

    Returns:
        Dict[str, Any]:
        - If the collection does not exist, returns a dictionary with the key "error" and the value "No such collection".
        - On successful update, returns a dictionary with the following keys:
            - status (str): The status of the update ("success")
            - collection_id (str): The ID of the collection
            - display_layout (str): The new display layout
    """
    coll = DB.get("collections", {}).get(collection_id)
    if not coll:
        return {"error": "No such collection"}
    coll["display_layout"] = display_layout
    return {"status": "success", "collection_id": collection_id, "display_layout": display_layout}

@tool_spec(
    spec={
        'name': 'update_collection_title',
        'description': 'Changes the title of a collection.',
        'parameters': {
            'type': 'object',
            'properties': {
                'collection_id': {
                    'type': 'string',
                    'description': 'The collection identifier.'
                },
                'title': {
                    'type': 'string',
                    'description': 'The new title for the collection.'
                }
            },
            'required': [
                'collection_id',
                'title'
            ]
        }
    }
)
def post_api_v1_collections_update_collection_title(collection_id: str, title: str) -> Dict[str, Any]:
    """
    Changes the title of a collection.

    Args:
        collection_id (str): The collection identifier.
        title (str): The new title for the collection.

    Returns:
        Dict[str, Any]:
        - If the collection does not exist, returns a dictionary with the key "error" and the value "No such collection".
        - On successful update, returns a dictionary with the following keys:
            - status (str): The status of the update ("success")
            - collection_id (str): The ID of the collection
            - new_title (str): The updated title
    """
    coll = DB.get("collections", {}).get(collection_id)
    if not coll:
        return {"error": "No such collection"}
    coll["title"] = title
    return {"status": "success", "collection_id": collection_id, "new_title": title}