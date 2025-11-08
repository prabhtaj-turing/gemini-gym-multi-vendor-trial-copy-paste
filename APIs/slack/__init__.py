"""
Slack API Simulation package.
"""

from . import AdminUsers
from . import Chat
from . import Conversations
from . import Files
from . import Reactions
from . import Reminders
from . import Search
from . import SimulationEngine
from . import Usergroups
from . import UsergroupUsers
from . import Users

import importlib
import os
import json
import tempfile
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.error_handling import get_package_error_mode
from common_utils.init_utils import create_error_simulator, resolve_function_import
from .SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "get_message_reactions": "slack.Reactions.get",
    "add_reaction_to_message": "slack.Reactions.add",
    "list_user_reactions": "slack.Reactions.list",
    "remove_reaction_from_message": "slack.Reactions.remove",
    "get_file_info": "slack.Files.get_file_info",
    "share_file": "slack.Files.share_file",
    "add_remote_file": "slack.Files.add_remote_file",
    "delete_file": "slack.Files.delete_file",
    "upload_file": "slack.Files.upload_file",
    "finish_external_file_upload": "slack.Files.finish_external_upload",
    "list_files": "slack.Files.list_files",
    "remove_remote_file": "slack.Files.remove_remote_file",
    "get_external_upload_url": "slack.Files.get_external_upload_url",
    "leave_conversation": "slack.Conversations.leave",
    "invite_to_conversation": "slack.Conversations.invite",
    "archive_conversation": "slack.Conversations.archive",
    "join_conversation": "slack.Conversations.join",
    "kick_from_conversation": "slack.Conversations.kick",
    "mark_conversation_read": "slack.Conversations.mark_read",
    "get_conversation_history": "slack.Conversations.history",
    "open_conversation": "slack.Conversations.open_conversation",
    "list_channels": "slack.Conversations.list_channels",
    "close_conversation": "slack.Conversations.close",
    "rename_conversation": "slack.Conversations.rename",
    "get_conversation_members": "slack.Conversations.members",
    "create_channel": "slack.Conversations.create_channel",
    "set_conversation_purpose": "slack.Conversations.setPurpose",
    "set_conversation_topic": "slack.Conversations.setConversationTopic",
    "get_conversation_replies": "slack.Conversations.replies",
    "create_user_group": "slack.Usergroups.create",
    "list_user_groups": "slack.Usergroups.list",
    "update_user_group": "slack.Usergroups.update",
    "disable_user_group": "slack.Usergroups.disable",
    "enable_user_group": "slack.Usergroups.enable",
    "search_messages": "slack.Search.search_messages",
    "search_files": "slack.Search.search_files",
    "search_all_content": "slack.Search.search_all",
    "send_me_message": "slack.Chat.meMessage",
    "delete_chat_message": "slack.Chat.delete",
    "delete_scheduled_message": "slack.Chat.deleteScheduledMessage",
    "post_ephemeral_message": "slack.Chat.postEphemeral",
    "post_chat_message": "slack.Chat.postMessage",
    "list_scheduled_messages": "slack.Chat.list_scheduled_Messages",
    "schedule_chat_message": "slack.Chat.scheduleMessage",
    "update_chat_message": "slack.Chat.update",
    "update_user_group_members": "slack.UsergroupUsers.update",
    "list_user_group_members": "slack.UsergroupUsers.list",
    "delete_reminder": "slack.Reminders.delete",
    "get_reminder_info": "slack.Reminders.info",
    "complete_reminder": "slack.Reminders.complete",
    "list_reminders": "slack.Reminders.list_reminders",
    "add_reminder": "slack.Reminders.add",
    "list_user_conversations": "slack.Users.conversations",
    "set_user_presence": "slack.Users.setPresence",
    "set_user_photo": "slack.Users.setPhoto",
    "delete_user_photo": "slack.Users.deletePhoto",
    "get_user_info": "slack.Users.info",
    "get_user_presence": "slack.Users.getPresence",
    "set_user_profile": "slack.Users.set_user_profile",
    "list_users": "slack.Users.list_users",
    "get_user_identity": "slack.Users.identity",
    "lookup_user_by_email": "slack.Users.lookupByEmail",
    "invite_admin_user": "slack.AdminUsers.invite",
    "get_current_user_id": "slack.Users.current_user_id",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
