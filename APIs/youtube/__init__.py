
# youtube/__init__.py
"""
youtube package for simulating YouTube API functionality.
"""

from . import Activities
from . import Caption
from . import Channels
from . import ChannelSection
from . import ChannelStatistics
from . import ChannelBanners
from . import Comment
from . import CommentThread
from . import Subscriptions
from . import VideoCategory
from . import Memberships
from . import Videos
from . import Search
from . import Playlists

import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from youtube.SimulationEngine import utils
from youtube import SimulationEngine

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "list_activities": "youtube.Activities.list",
  "list_video_categories": "youtube.VideoCategory.list",
  "create_comment_thread": "youtube.CommentThread.insert",
  "list_comment_threads": "youtube.CommentThread.list",
  "delete_comment_thread": "youtube.CommentThread.delete",
  "update_comment_thread": "youtube.CommentThread.update",
  "list_searches": "youtube.Search.list",
  "list_channel_sections": "youtube.ChannelSection.list",
  "delete_channel_section": "youtube.ChannelSection.delete",
  "insert_channel_section": "youtube.ChannelSection.insert",
  "update_channel_section": "youtube.ChannelSection.update",
  "list_channels": "youtube.Channels.list",
  "create_channel": "youtube.Channels.insert",
  "update_channel_metadata": "youtube.Channels.update",
  "list_memberships": "youtube.Memberships.list",
  "create_membership": "youtube.Memberships.insert",
  "delete_membership": "youtube.Memberships.delete",
  "update_membership": "youtube.Memberships.update",
  "set_comment_moderation_status": "youtube.Comment.set_moderation_status",
  "delete_comment": "youtube.Comment.delete",
  "add_comment": "youtube.Comment.insert",
  "list_comments": "youtube.Comment.list",
  "mark_comment_as_spam": "youtube.Comment.mark_as_spam",
  "update_comment": "youtube.Comment.update",
  "delete_caption": "youtube.Caption.delete",
  "download_caption": "youtube.Caption.download",
  "insert_caption": "youtube.Caption.insert",
  "list_captions": "youtube.Caption.list",
  "update_caption": "youtube.Caption.update",
  "list_videos": "youtube.Videos.list",
  "rate_video": "youtube.Videos.rate",
  "report_video_abuse": "youtube.Videos.report_abuse",
  "delete_video": "youtube.Videos.delete",
  "update_video_metadata": "youtube.Videos.update",
  "upload_video": "youtube.Videos.upload",
  "manage_channel_comment_count": "youtube.ChannelStatistics.comment_count",
  "manage_channel_subscriber_visibility": "youtube.ChannelStatistics.hidden_subscriber_count",
  "manage_channel_subscriber_count": "youtube.ChannelStatistics.subscriber_count",
  "manage_channel_video_count": "youtube.ChannelStatistics.video_count",
  "manage_channel_view_count": "youtube.ChannelStatistics.view_count",
  "insert_channel_banner": "youtube.ChannelBanners.insert",
  "create_subscription": "youtube.Subscriptions.insert",
  "delete_subscription": "youtube.Subscriptions.delete",
  "list_subscriptions": "youtube.Subscriptions.list",
  "list_playlists": "youtube.Playlists.list_playlists",
  "get_playlist": "youtube.Playlists.get",
  "create_playlist": "youtube.Playlists.create",
  "update_playlist": "youtube.Playlists.update",
  "delete_playlist": "youtube.Playlists.delete",
  "add_video_to_playlist": "youtube.Playlists.add_video",
  "delete_video_from_playlist": "youtube.Playlists.delete_video",
  "reorder_playlist_videos": "youtube.Playlists.reorder"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
