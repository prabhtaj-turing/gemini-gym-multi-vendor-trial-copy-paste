
class AppNotFoundError(Exception):
    """Raised when an application is not found on the device."""
    pass

class AppNameAndPackageMismatchError(Exception):
    """Raised when the app name and package name do not match."""
    pass

class NoDefaultBrowserError(Exception):
    """Raised when no default browser is set on the device."""
    pass

class NoDefaultCameraError(Exception):
    """Raised when no default camera is set on the device."""
    pass

class DevicePoweredOffError(Exception):
    """Raised when the device is powered off."""
    pass