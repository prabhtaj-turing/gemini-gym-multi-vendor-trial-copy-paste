
# APIs/hubspot/__init__.py

from .SimulationEngine.db import DB, load_state, save_state
from hubspot.SimulationEngine import utils

from . import Campaigns
from . import Forms
from . import FormGlobalEvents
from . import MarketingEmails
from . import MarketingEvents
from . import SingleSend
from . import Templates
from . import TransactionalEmails
from . import SimulationEngine
import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "get_templates": "hubspot.Templates.get_templates",
  "create_template": "hubspot.Templates.create_template",
  "get_template_by_id": "hubspot.Templates.get_template_by_id",
  "update_template_by_id": "hubspot.Templates.update_template_by_id",
  "delete_template_by_id": "hubspot.Templates.delete_template_by_id",
  "restore_deleted_template": "hubspot.Templates.restore_deleted_template",
  "get_forms": "hubspot.Forms.get_forms",
  "create_form": "hubspot.Forms.create_form",
  "get_form_by_id": "hubspot.Forms.get_form",
  "update_form": "hubspot.Forms.update_form",
  "delete_form": "hubspot.Forms.delete_form",
  "get_marketing_events": "hubspot.MarketingEvents.get_events",
  "create_marketing_event": "hubspot.MarketingEvents.create_event",
  "get_marketing_event_by_id": "hubspot.MarketingEvents.get_event",
  "delete_marketing_event": "hubspot.MarketingEvents.delete_event",
  "update_marketing_event": "hubspot.MarketingEvents.update_event",
  "cancel_marketing_event": "hubspot.MarketingEvents.cancel_event",
  "create_or_update_marketing_event_attendee": "hubspot.MarketingEvents.create_or_update_attendee",
  "get_marketing_event_attendees": "hubspot.MarketingEvents.get_attendees",
  "delete_marketing_event_attendee": "hubspot.MarketingEvents.delete_attendee",
  "send_single_email_with_template": "hubspot.SingleSend.sendSingleEmail",
  "send_transactional_email": "hubspot.TransactionalEmails.sendSingleEmail",
  "get_form_global_event_subscription_definitions": "hubspot.FormGlobalEvents.get_subscription_definitions",
  "create_form_global_event_subscription": "hubspot.FormGlobalEvents.create_subscription",
  "get_form_global_event_subscriptions": "hubspot.FormGlobalEvents.get_subscriptions",
  "delete_form_global_event_subscription": "hubspot.FormGlobalEvents.delete_subscription",
  "update_form_global_event_subscription": "hubspot.FormGlobalEvents.update_subscription",
  "get_campaigns": "hubspot.Campaigns.get_campaigns",
  "create_campaign": "hubspot.Campaigns.create_campaign",
  "get_campaign_by_id": "hubspot.Campaigns.get_campaign",
  "update_campaign": "hubspot.Campaigns.update_campaign",
  "archive_campaign": "hubspot.Campaigns.archive_campaign",
  "create_marketing_email": "hubspot.MarketingEmails.create",
  "get_marketing_email_by_id": "hubspot.MarketingEmails.getById",
  "update_marketing_email": "hubspot.MarketingEmails.update",
  "delete_marketing_email": "hubspot.MarketingEmails.delete",
  "clone_marketing_email": "hubspot.MarketingEmails.clone"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
