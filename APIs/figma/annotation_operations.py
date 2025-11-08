from common_utils.tool_spec_decorator import tool_spec
import datetime
import uuid
import inspect
from typing import Optional, List, Dict, Any

from .SimulationEngine.db import DB
from .SimulationEngine import utils # Per instruction, though not directly used in this function
from .SimulationEngine import models # Per instruction, though not directly used in this function
from .SimulationEngine import custom_errors
from .SimulationEngine import utils
from pydantic import ValidationError as PydanticBuiltInValidationError


@tool_spec(
    spec={
        'name': 'get_annotations',
        'description': """ Get all annotations in the current document or specific node.
        
        This function retrieves all annotations. If the `nodeId` parameter is provided,
        it fetches annotations specifically for the node identified by that ID.
        If `nodeId` is omitted, the function returns annotations from the entire
        current document. If the `includeCategories` parameter is true, and an
        annotation has a 'categoryId', the full category object is included with
        that annotation's details. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'nodeId': {
                    'type': 'string',
                    'description': """ The ID of a specific node for which to retrieve
                    annotations. Defaults to None. If omitted, annotations from the entire 
                    current document are returned. """
                },
                'includeCategories': {
                    'type': 'boolean',
                    'description': """ If true, the full category object
                    will be included for each annotation that has a 'categoryId'.
                    Defaults to false if not provided. """
                }
            },
            'required': []
        }
    }
)
def get_annotations(nodeId: Optional[str] = None, includeCategories: Optional[bool] = False) -> List[Dict[str, Any]]:
    """Get all annotations in the current document or specific node.

    This function retrieves all annotations. If the `nodeId` parameter is provided,
    it fetches annotations specifically for the node identified by that ID.
    If `nodeId` is omitted, the function returns annotations from the entire
    current document. If the `includeCategories` parameter is true, and an
    annotation has a 'categoryId', the full category object is included with
    that annotation's details.

    Args:
        nodeId (Optional[str]): The ID of a specific node for which to retrieve
            annotations. Defaults to None. If omitted, annotations from the entire 
            current document are returned.
        includeCategories (Optional[bool]): If true, the full category object
            will be included for each annotation that has a 'categoryId'.
            Defaults to false if not provided.

    Returns:
        List[Dict[str, Any]]: A list of annotation objects. Each dictionary in the
            list represents an annotation and contains the following keys:
            'annotationId' (str): The unique identifier of the annotation.
            'nodeId' (str): The ID of the node to which this annotation is attached.
            'labelMarkdown' (str): The content of the annotation in Markdown format.
            'categoryId' (Optional[str]): ID of the category this annotation
                belongs to, if any.
            'category' (Optional[Dict[str, Any]]): Detailed information about the
                category. This field is included if the 'includeCategories' input
                parameter is true and 'categoryId' is set. If present, this
                dictionary contains:
                'id' (str): Category ID.
                'name' (str): Category name.
                'color' (str): Category color code (e.g., hex).
            'properties' (Optional[List[Dict[str, Any]]]): A list of custom
                key-value property objects associated with the annotation. Each
                dictionary in this list represents a property object and contains:
                'name' (str): Name/key of the property.
                'value' (Any): Value of the property.

    Raises:
        NodeNotFoundError: If a specific 'nodeId' is provided and that node
            does not exist.
        PluginError: If there is an internal issue or error within the plugin
            while retrieving annotations.
        ValidationError: If input arguments fail validation.
    """
    # 1. Input Validation
    if nodeId is not None and not isinstance(nodeId, str):
        raise custom_errors.ValidationError("Argument 'nodeId' must be of type string.")
    if includeCategories is not None and not isinstance(includeCategories, bool):
        raise custom_errors.ValidationError("Argument 'includeCategories' must be of type boolean.")

    try:
        # 2. Get Current File and Document
        current_file = utils.get_current_file()
        if not current_file:
            raise custom_errors.PluginError("Could not retrieve the current file.")
        document_root = current_file.get('document')
        if not document_root:
            raise custom_errors.PluginError("Current file has no document.")

        # 3. Collect Annotations
        source_annotations = []
        if nodeId:
            target_node = utils.find_node_by_id(document_root.get('children', []), nodeId)
            if not target_node:
                raise custom_errors.NodeNotFoundError(f"Node with ID '{nodeId}' not found.")
            
            for ann in target_node.get('annotations', []):
                ann_with_context = ann.copy()
                ann_with_context['nodeId'] = nodeId
                source_annotations.append(ann_with_context)
        else:
            utils._collect_annotations_recursively(document_root, source_annotations)

        # 4. Process Annotations for Final Output
        processed_annotations: List[Dict[str, Any]] = []
        file_categories = {cat['id']: cat for cat in current_file.get('annotation_categories', [])}

        for ann in source_annotations:
            if not all(k in ann for k in ['annotationId', 'labelMarkdown', 'nodeId']):
                 raise custom_errors.PluginError("Malformed annotation data in DB.")

            annotation_dict = {
                'annotationId': ann.get('annotationId'),
                'nodeId': ann.get('nodeId'),
                'labelMarkdown': ann.get('labelMarkdown'),
                'categoryId': ann.get('categoryId'),
                'properties': ann.get('properties')
            }
            
            if includeCategories and annotation_dict['categoryId']:
                category_data = file_categories.get(annotation_dict['categoryId'])
                if (category_data and 
                        'id' in category_data and 
                        'name' in category_data and 
                        'color' in category_data):
                    annotation_dict['category'] = {
                        'id': category_data['id'],
                        'name': category_data['name'],
                        'color': utils._rgba_to_hex(category_data.get('color', {}))
                } 
                else:
                    # If category data is missing or malformed, set category to None.
                    annotation_dict['category'] = None
            
            processed_annotations.append(annotation_dict)
            
        return processed_annotations

    except (custom_errors.NodeNotFoundError, custom_errors.ValidationError) as e:
        raise e
    except Exception as e:
        raise custom_errors.PluginError(f"An internal plugin error occurred: {e}")


@tool_spec(
    spec={
        'name': 'set_annotation',
        'description': """ Create or update an annotation.
        
        This function creates a new annotation or updates an existing one. It associates an
        annotation with a specific `nodeId`. The annotation's content is provided via
        `labelMarkdown`. Optionally, an `annotationId` can be specified for updates,
        a `categoryId` for classification, and custom `properties` can be added.
        The function returns a dictionary containing details of the created or updated
        annotation. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'nodeId': {
                    'type': 'string',
                    'description': 'The ID of the node to which this annotation is attached.'
                },
                'labelMarkdown': {
                    'type': 'string',
                    'description': 'The content of the annotation, formatted as Markdown.'
                },
                'annotationId': {
                    'type': 'string',
                    'description': """ The unique identifier of the annotation to update.
                    If `None`, a new annotation will be created. Defaults to `None`. """
                },
                'categoryId': {
                    'type': 'string',
                    'description': """ The ID of an existing category to assign to this
                    annotation. Defaults to `None`. """
                },
                'properties': {
                    'type': 'array',
                    'description': """ A list of custom key-value
                    properties to associate with the annotation. Defaults to `None`. Each dictionary in the list
                    should contain the following keys: """,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {
                                'type': 'string',
                                'description': 'Property name.'
                            },
                            'value': {
                                'type': 'string',
                                'description': """ Property value. Possible values are:
                                     width;
                                    height;
                                    maxWidth;
                                    minWidth;
                                    maxHeight;
                                    minHeight;
                                    fills;
                                    strokes;
                                    effects;
                                    strokeWeight;
                                    cornerRadius;
                                    textStyleId;
                                    textAlignHorizontal;
                                    fontFamily;
                                    fontStyle;
                                    fontSize;
                                    fontWeight;
                                    lineHeight;
                                    letterSpacing;
                                    itemSpacing;
                                    padding;
                                    layoutMode;
                                    alignItems;
                                    opacity;
                                    mainComponent;
                                    gridRowGap;
                                    gridColumnGap;
                                    gridRowCount;
                                    gridColumnCount;
                                    gridRowAnchorIndex;
                                    gridColumnAnchorIndex;
                                    gridRowSpan;
                                    gridColumnSpan. """
                            }
                        },
                        'required': [
                            'name',
                            'value'
                        ]
                    }
                }
            },
            'required': [
                'nodeId',
                'labelMarkdown'
            ]
        }
    }
)
def set_annotation(nodeId: str, 
                   labelMarkdown: str, 
                   annotationId: Optional[str] = None, 
                   categoryId: Optional[str] = None, 
                   properties: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """Create or update an annotation.

    This function creates a new annotation or updates an existing one. It associates an
    annotation with a specific `nodeId`. The annotation's content is provided via
    `labelMarkdown`. Optionally, an `annotationId` can be specified for updates,
    a `categoryId` for classification, and custom `properties` can be added.
    The function returns a dictionary containing details of the created or updated
    annotation.

    Args:
        nodeId (str): The ID of the node to which this annotation is attached.
        labelMarkdown (str): The content of the annotation, formatted as Markdown.
        annotationId (Optional[str]): The unique identifier of the annotation to update.
            If `None`, a new annotation will be created. Defaults to `None`.
        categoryId (Optional[str]): The ID of an existing category to assign to this
            annotation. Defaults to `None`.
        properties (Optional[List[Dict[str, str]]]): A list of custom key-value
            properties to associate with the annotation. Defaults to `None`. Each dictionary in the list
            should contain the following keys:
            name (str): Property name.
            value (str): Property value. Possible values are:
                width;
                height;
                maxWidth;
                minWidth;
                maxHeight;
                minHeight;
                fills;
                strokes;
                effects;
                strokeWeight;
                cornerRadius;
                textStyleId;
                textAlignHorizontal;
                fontFamily;
                fontStyle;
                fontSize;
                fontWeight;
                lineHeight;
                letterSpacing;
                itemSpacing;
                padding;
                layoutMode;
                alignItems;
                opacity;
                mainComponent;
                gridRowGap;
                gridColumnGap;
                gridRowCount;
                gridColumnCount;
                gridRowAnchorIndex;
                gridColumnAnchorIndex;
                gridRowSpan;
                gridColumnSpan.

    Returns:
        Dict[str, Any]: Details of the created or updated annotation. Contains the
            following keys:
            annotationId (str): The unique identifier of the annotation (newly created or
                updated).
            nodeId (str): The ID of the node this annotation is attached to.
            labelMarkdown (str): The content of the annotation.
            categoryId (Optional[str]): ID of the assigned category.
            properties (Optional[List[Dict[str, Any]]]): A list of custom key-value [{<any-key>:<value>}]
                properties. Each property in the list is a dictionary containing:
                name (str): Property name.
                value (Union[str, int, float, bool, None]): Property value (arbitrary JSON-serializable structure).

    Raises:
        NodeNotFoundError: If the specified nodeId does not exist.
        AnnotationNotFoundError: If annotationId is provided for an update, but no
            annotation with that ID exists for the given nodeId.
        CategoryNotFoundError: If categoryId is provided but does not correspond to an
            existing category.
        InvalidInputError: If labelMarkdown is empty, or properties are malformed.
        FigmaOperationError: If there is an issue setting the annotation.
        ValidationError: If input arguments fail validation.
    """
    # 1. Input Validation
    if not isinstance(nodeId, str) or not nodeId.strip():
        raise custom_errors.InvalidInputError("nodeId must be a non-empty string.")
    if not isinstance(labelMarkdown, str) or not labelMarkdown.strip():
        raise custom_errors.InvalidInputError("labelMarkdown cannot be empty.")

    # Validate annotationId if provided
    if annotationId is not None:
        if not isinstance(annotationId, str):
            raise custom_errors.InvalidInputError("annotationId must be a string.")
        if not annotationId.strip():
            raise custom_errors.InvalidInputError("annotationId cannot be empty.")

    # Validate categoryId if provided
    if categoryId is not None:
        if not isinstance(categoryId, str):
            raise custom_errors.InvalidInputError("categoryId must be a string.")
        if not categoryId.strip():
            raise custom_errors.InvalidInputError("categoryId cannot be empty.")

    if properties is not None:
        if not isinstance(properties, list):
            raise custom_errors.InvalidInputError("Properties must be a list of dictionaries.")
        for i, prop in enumerate(properties):
            if not isinstance(prop, dict) or 'name' not in prop or 'value' not in prop:
                 raise custom_errors.InvalidInputError(f"Malformed property at index {i}. Must be a dict with 'name' and 'value'.")
            # Validate the 'name' field in properties
            if not isinstance(prop['name'], str):
                raise custom_errors.InvalidInputError(f"Property name at index {i} must be a string.")
            if not prop['name'].strip():
                raise custom_errors.InvalidInputError(f"Property name at index {i} cannot be empty.")
            
            # Validate the 'value' field in properties
            value = prop['value']
            # Check if value is JSON-serializable (basic types, dict, list)
            if not isinstance(value, (str, int, float, bool, type(None), dict, list)):
                raise custom_errors.InvalidInputError(f"Property value at index {i} must be JSON-serializable (str, int, float, bool, None, dict, or list).")

    try:
        # 2. Get File and Node
        current_file = utils.get_current_file()
        if not current_file:
            raise custom_errors.FigmaOperationError("Could not retrieve the current file.")
        document_root = current_file.get('document')
        if not document_root:
            raise custom_errors.FigmaOperationError("Current file has no document.")
        
        target_node = utils.find_node_by_id(document_root.get('children', []), nodeId)
        if not target_node:
            raise custom_errors.NodeNotFoundError(f"Node with ID '{nodeId}' not found.")
        
        # 3. Validate Category ID
        if categoryId:
            if not any(cat['id'] == categoryId for cat in current_file.get('annotation_categories', [])):
                raise custom_errors.CategoryNotFoundError(f"Category with ID '{categoryId}' not found.")

        # Ensure the node has an 'annotations' list
        if 'annotations' not in target_node:
            target_node['annotations'] = []
        
        # 5. Create or Update Logic
        if annotationId is None:
            # Create new annotation
            new_id = str(uuid.uuid4())
            annotation_data = {
                "annotationId": new_id,
                "labelMarkdown": labelMarkdown,
                "categoryId": categoryId,
                "properties": properties
            }
            target_node['annotations'].append(annotation_data)
            return_data = annotation_data
        else:
            # Update existing annotation
            existing_annotation = next((ann for ann in target_node['annotations'] if ann.get('annotationId') == annotationId), None)
            
            if not existing_annotation:
                raise custom_errors.AnnotationNotFoundError(f"Annotation with ID '{annotationId}' not found on node '{nodeId}'.")

            existing_annotation.update({
                'labelMarkdown': labelMarkdown,
                'categoryId': categoryId,
                'properties': properties
            })
            return_data = existing_annotation
        
        # 6. Construct and return result matching the docstring
        return {
            "annotationId": return_data['annotationId'],
            "nodeId": nodeId,
            "labelMarkdown": return_data['labelMarkdown'],
            "categoryId": return_data.get('categoryId'),
            "properties": return_data.get('properties')
        }

    except (custom_errors.ValidationError, custom_errors.InvalidInputError, custom_errors.NodeNotFoundError, custom_errors.AnnotationNotFoundError, custom_errors.CategoryNotFoundError) as e:
        raise e
    except Exception as e:
        raise custom_errors.FigmaOperationError(f"An unexpected error occurred: {e}")
