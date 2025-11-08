class AppointmentNotFoundError(Exception):
    """Custom error for appointment not found."""
    pass

class InvalidPostalCodeError(Exception):
    """Custom error for invalid postal code."""
    pass

class InvalidStartDateError(Exception):
    """Custom error for invalid start date."""
    pass

class VisitNotFoundError(Exception):
    """Custom error for visit id not found."""
    pass

class SlotNotFoundError(Exception):
    """Custom error for slot id not found."""
    pass

class TechnicianVisitNotFoundError(Exception):
    """Custom error for technician visit not found."""
    pass

class InvalidServiceTypeError(Exception):
    """Custom error for invalid service type."""
    pass

class ActivationAttemptNotFoundError(Exception):
    """Custom error for activation attempt not found."""
    pass

class DuplicateAppointmentError(Exception):
    """Custom error for duplicate appointment."""
    pass

class ValidationError(Exception):
    """Custom error for validation errors."""
    pass

class EnvironmentError(Exception):
    """Custom error for no API key found."""
    pass

class TemplateNotFoundError(Exception):
    """Custom error for template not found."""
    pass