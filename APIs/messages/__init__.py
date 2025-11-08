# messages/__init__.py
# Import the main modules and resources
from typing import Any, Dict, List, Optional, Union
from .SimulationEngine.db import DB, load_state, save_state
from messages.SimulationEngine import utils
from .SimulationEngine.models import (
    validate_send_chat_message, 
    validate_prepare_chat_message,
    validate_show_recipient_choices,
    validate_ask_for_message_body,
    Recipient,
    MediaAttachment,
    Observation
)
from .SimulationEngine.utils import _next_counter
from .SimulationEngine.custom_errors import (
    InvalidRecipientError,
    MessageBodyRequiredError,
    InvalidPhoneNumberError,
    InvalidMediaAttachmentError
)
import os
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from messages import SimulationEngine

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "send_chat_message": "messages.messages.send_chat_message",
  "prepare_chat_message": "messages.messages.prepare_chat_message",
  "show_message_recipient_choices": "messages.messages.show_message_recipient_choices",
  "ask_for_message_body": "messages.messages.ask_for_message_body",
  "show_message_recipient_not_found_or_specified": "messages.messages.show_message_recipient_not_found_or_specified",

}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())