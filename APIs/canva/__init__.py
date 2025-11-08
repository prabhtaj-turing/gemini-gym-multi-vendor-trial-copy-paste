# canva/__init__.py
from . import Canva
from . import SimulationEngine
from .Canva import Design
from .Canva.Design import Comment, DesignExport, DesignImport
from .Canva import BrandTemplate
from .Canva import Autofill
from .Canva import Asset
from .Canva import Folder
from .Canva import Users
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.error_handling import get_package_error_mode

import os
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode

from canva.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
                "create_autofill_job": "canva.Canva.Autofill.create_autofill_job", 
                 "get_autofill_job": "canva.Canva.Autofill.get_autofill_job", 
                 "create_folder": "canva.Canva.Folder.create_folder", 
                 "get_folder": "canva.Canva.Folder.get_folder", 
                 "update_folder": "canva.Canva.Folder.update_folder", 
                 "delete_folder": "canva.Canva.Folder.delete_folder",
                 "list_folder_items": "canva.Canva.Folder.list_folder_items", 
                 "get_brand_template": "canva.Canva.BrandTemplate.get_brand_template", 
                 "get_brand_template_dataset": "canva.Canva.BrandTemplate.get_brand_template_dataset", 
                 "list_brand_templates": "canva.Canva.BrandTemplate.list_brand_templates", 
                 "create_asset_upload_job": "canva.Canva.Asset.create_asset_upload_job", 
                 "get_asset_upload_job": "canva.Canva.Asset.get_asset_upload_job", 
                 "get_asset": "canva.Canva.Asset.get_asset", 
                 "update_asset": "canva.Canva.Asset.update_asset", 
                 "delete_asset": "canva.Canva.Asset.delete_asset", 
                 "get_current_user": "canva.Canva.Users.get_current_user", 
                 "get_current_user_profile": "canva.Canva.Users.get_current_user_profile", 
                 "create_design_export_job": "canva.Canva.Design.DesignExport.create_design_export_job", 
                 "get_design_export_job": "canva.Canva.Design.DesignExport.get_design_export_job", 
                 "create_design": "canva.Canva.Design.DesignCreation.create_design", 
                 "list_designs": "canva.Canva.Design.DesignListing.list_designs", 
                 "get_design": "canva.Canva.Design.DesignRetrieval.get_design", 
                 "get_design_pages": "canva.Canva.Design.DesignRetrieval.get_design_pages", 
                 "create_comment_thread": "canva.Canva.Design.Comment.create_thread", 
                 "create_comment_reply": "canva.Canva.Design.Comment.create_reply", 
                 "get_comment_thread": "canva.Canva.Design.Comment.get_thread", 
                 "get_comment_reply": "canva.Canva.Design.Comment.get_reply", 
                 "list_comment_replies": "canva.Canva.Design.Comment.list_replies", 
                 "create_design_import_job": "canva.Canva.Design.DesignImport.create_design_import",
                 "get_design_import_job": "canva.Canva.Design.DesignImport.get_design_import_job", 
                 "create_url_design_import_job": "canva.Canva.Design.DesignImport.create_url_import_job", 
                 "get_url_design_import_job": "canva.Canva.Design.DesignImport.get_url_import_job"
                 }

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    global _function_map
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
