# generic_messages/__init__.py
# Import the main modules and resources
from typing import Any, Dict, List, Optional, Union
from generic_messages.SimulationEngine import utils
from .SimulationEngine.models import (
    validate_send, 
    validate_show_recipient_choices,
    validate_ask_for_message_body,
    Recipient,
    Endpoint,
    MediaAttachment,
    Observation
)
from .SimulationEngine.custom_errors import (
    InvalidRecipientError,
    InvalidEndpointError,
    MessageBodyRequiredError,
    InvalidMediaAttachmentError,
    RecipientNotFoundError
)
import os
from common_utils.error_handling import get_package_error_mode
from common_utils.init_utils import create_error_simulator, resolve_function_import
from generic_messages import SimulationEngine

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "send": "generic_messages.message_controller.send",
  "show_message_recipient_choices": "generic_messages.message_controller.show_message_recipient_choices",
  "ask_for_message_body": "generic_messages.message_controller.ask_for_message_body",
  "show_message_recipient_not_found_or_specified": "generic_messages.message_controller.show_message_recipient_not_found_or_specified",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())

