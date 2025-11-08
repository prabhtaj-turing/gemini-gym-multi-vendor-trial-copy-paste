# gmail/__init__.py
# Import the main 'users' module itself. This allows access to functions defined
# directly in users/__init__.py like getProfile via:
#   gmail.users.getProfile()
from . import Users

# --- Top-Level Resources from 'users' ---
# Import primary resource modules from the 'users' submodule to expose them directly.
# e.g., gmail.threads.list(), gmail_api.messages.get()
from .Users import Threads
from .Users import Messages
from .Users import Labels
from .Users import History
from .Users import Drafts

# --- Resources from 'SimulationEngine' ---
from .SimulationEngine.db import DB, load_state, save_state
from .SimulationEngine import utils

# --- Resources from 'Users.Messages' ---
# Import specific resources from within 'Messages'.
# e.g., gmail.attachments.get()
from .Users.Messages import Attachments

# --- Resources from 'Users.Settings' ---
# Import specific setting resource modules from the 'Users.Settings' sub-package.
# e.g., gmail.vacation.getVacation(), gmail.imap.getImap()
from .Users.Settings import Vacation
from .Users.Settings import Imap
from .Users.Settings import Language
from .Users.Settings import Pop
from .Users.Settings import AutoForwarding

# We don't import 'send_as' itself, but its contents directly:
from .Users.Settings.SendAs import SmimeInfo  # Import smime_info from within send_as

# Define __all__ for 'from gmail import *'
# Explicitly lists the public API components intended for import *.
import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from common_utils.init_utils import apply_decorators, create_error_simulator, resolve_function_import

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "trash_thread": "gmail.Users.Threads.trash",
  "untrash_thread": "gmail.Users.Threads.untrash",
  "delete_thread": "gmail.Users.Threads.delete",
  "get_thread": "gmail.Users.Threads.get",
  "list_threads": "gmail.Users.Threads.list",
  "modify_thread_labels": "gmail.Users.Threads.modify",
  "get_user_profile": "gmail.Users.getProfile",
  "watch_user_mailbox": "gmail.Users.watch",
  "stop_mailbox_watch": "gmail.Users.stop",
  "check_user_exists": "gmail.Users.exists",
  "create_user": "gmail.Users.createUser",
  "create_label": "gmail.Users.Labels.create",
  "delete_label": "gmail.Users.Labels.delete",
  "get_label": "gmail.Users.Labels.get",
  "list_labels": "gmail.Users.Labels.list",
  "update_label": "gmail.Users.Labels.update",
  "patch_label": "gmail.Users.Labels.patch",
  "create_draft": "gmail.Users.Drafts.create",
  "list_drafts": "gmail.Users.Drafts.list",
  "update_draft": "gmail.Users.Drafts.update",
  "delete_draft": "gmail.Users.Drafts.delete",
  "get_draft": "gmail.Users.Drafts.get",
  "send_draft": "gmail.Users.Drafts.send",
  "list_history_records": "gmail.Users.History.list",
  "get_auto_forwarding_settings": "gmail.Users.Settings.AutoForwarding.getAutoForwarding",
  "update_auto_forwarding_settings": "gmail.Users.Settings.AutoForwarding.updateAutoForwarding",
  "get_vacation_settings": "gmail.Users.Settings.Vacation.getVacation",
  "update_vacation_settings": "gmail.Users.Settings.Vacation.updateVacation",
  "get_imap_settings": "gmail.Users.Settings.Imap.getImap",
  "update_imap_settings": "gmail.Users.Settings.Imap.updateImap",
  "get_language_settings": "gmail.Users.Settings.Language.getLanguage",
  "update_language_settings": "gmail.Users.Settings.Language.updateLanguage",
  "get_pop_settings": "gmail.Users.Settings.Pop.getPop",
  "update_pop_settings": "gmail.Users.Settings.Pop.updatePop",
  "list_send_as_smime_info": "gmail.Users.Settings.SendAs.SmimeInfo.list",
  "get_send_as_smime_info": "gmail.Users.Settings.SendAs.SmimeInfo.get",
  "insert_send_as_smime_info": "gmail.Users.Settings.SendAs.SmimeInfo.insert",
  "update_send_as_smime_info": "gmail.Users.Settings.SendAs.SmimeInfo.update",
  "patch_send_as_smime_info": "gmail.Users.Settings.SendAs.SmimeInfo.patch",
  "delete_send_as_smime_info": "gmail.Users.Settings.SendAs.SmimeInfo.delete",
  "set_default_send_as_smime_info": "gmail.Users.Settings.SendAs.SmimeInfo.setDefault",
  "list_send_as_aliases": "gmail.Users.Settings.SendAs.list",
  "get_send_as_alias": "gmail.Users.Settings.SendAs.get",
  "create_send_as_alias": "gmail.Users.Settings.SendAs.create",
  "update_send_as_alias": "gmail.Users.Settings.SendAs.update",
  "patch_send_as_alias": "gmail.Users.Settings.SendAs.patch",
  "delete_send_as_alias": "gmail.Users.Settings.SendAs.delete",
  "verify_send_as_alias": "gmail.Users.Settings.SendAs.verify",
  "trash_message": "gmail.Users.Messages.trash",
  "untrash_message": "gmail.Users.Messages.untrash",
  "delete_message": "gmail.Users.Messages.delete",
  "batch_delete_messages": "gmail.Users.Messages.batchDelete",
  "import_message": "gmail.Users.Messages.import_",
  "insert_message": "gmail.Users.Messages.insert",
  "get_message": "gmail.Users.Messages.get",
  "send_message": "gmail.Users.Messages.send",
  "list_messages": "gmail.Users.Messages.list",
  "modify_message_labels": "gmail.Users.Messages.modify",
  "batch_modify_message_labels": "gmail.Users.Messages.batchModify",
  "get_message_attachment": "gmail.Users.Messages.Attachments.get"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
