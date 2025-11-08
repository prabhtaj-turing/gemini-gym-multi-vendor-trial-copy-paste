class SceneNotFoundError(Exception): pass
class ObjectNotFoundError(Exception): pass
class MaterialNotFoundError(Exception): pass
class AssetNotFoundError(Exception): pass
class JobNotFoundError(Exception): pass
class InvalidStateError(Exception): pass
class DuplicateNameError(Exception): pass
class InvalidAssetTypeError(Exception):pass
class InvalidInputError(Exception): pass
class ValidationError(Exception): pass
class DownloadError(Exception): pass
class BlenderImportError(Exception): pass
class Hyper3DAPIError(Exception): pass
class AssetNotReadyError(Exception): pass

class InvalidDateTimeFormatError(Exception):
    """Raised when a datetime string is not in the expected format."""
    pass