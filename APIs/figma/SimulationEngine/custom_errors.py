from typing import Any, Optional
class FigmaError(Exception):
    """Base class for Figma related errors."""
    pass

class NoSelectionError(Exception):
    """
    Raised when no nodes are currently selected in the Figma document.
    """
    pass

class FigmaOperationError(Exception):
    """
    Raised when there is an issue communicating with the Figma plugin environment.
    """
    pass

class NodeTypeError(Exception):
    """Raised when a node type does not support a specific operation (e.g., fill color)."""
    pass

class InvalidColorError(Exception):
    """Raised when any of the color component values (r, g, b, a) are outside the valid range (0.0 to 1.0)."""
    pass

class ValidationError(Exception):
    """Raised when input arguments fail validation."""
    pass

class PluginError(Exception):
    """Raised when there is an internal issue or error within the plugin."""
    pass
class AnnotationNotFoundError(Exception):
    """Raised when annotationId is provided for an update, but no
    annotation with that ID exists for the given nodeId."""
    pass

class CategoryNotFoundError(Exception):
    """Raised when categoryId is provided but does not correspond to an
    existing category."""
    pass

class InvalidInputError(Exception):
    """Raised if the layout_mode value is not a valid mode (e.g., 'NONE', 'HORIZONTAL', 'VERTICAL') 
    or if layout_wrap (when provided) is not a valid wrap behavior (e.g., 'NO_WRAP', 'WRAP')."""
    pass
class ParentNotFoundError(Exception):
    """
    Raised if the specified `parent_id` does not correspond to a valid,
    existing container node in Figma.
    """
    pass

class NoDocumentOpenError(Exception):
    """Raised when no Figma document is currently open or accessible."""
    pass
class NodeNotFoundError(Exception):
    """Raised when a specific 'nodeId' is provided and that node does not exist."""
    pass

class NotFoundError(Exception):
    """
    Raised if the file with the given file_key or any specified node_id does not exist.
    """
    pass

class DownloadError(Exception):
    """
    Raised if an error occurs during the image download process for one or more nodes.
    """
    pass

class CloneError(Exception):
    """
    Raised if the node cannot be cloned (e.g., it's a special type
    like the document root, or is locked in a way that prevents
    cloning).
    """
    pass

class FigmaDownloaderError(Exception):
    """Base exception for figma image downloader errors."""
    pass

class ResizeError(Exception):
    """
    Raised if the specified node cannot be resized.
    Common reasons include the node being locked, being part of an auto-layout
    frame that dictates its size, or the node type itself not supporting
    arbitrary resizing.
    """
    pass

class DeleteError(Exception):
    """Raised when a node cannot be deleted (e.g., it is locked or a critical system node)."""
    pass

class NodeTypeSupportError(Exception):
    """Raised if the specified node type does not support the operation (e.g., strokes)."""
    pass
