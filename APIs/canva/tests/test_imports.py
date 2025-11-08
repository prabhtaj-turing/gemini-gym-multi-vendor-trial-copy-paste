import unittest
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import _function_map
import importlib
from .. import get_design
import typing
from pydantic import BaseModel

class TestImports(BaseTestCaseWithErrorHandler):
    """
    Test suite for validating the Pydantic models.
    """

    def test_import_canva_package(self):
        """
        Test that the canva package can be imported successfully.
        """
        try:    
            import APIs.canva
        except ImportError:
            self.fail("Failed to import APIs.canva package")

    def test_import_public_functions(self):
        """
        Test that the public functions can be imported successfully.
        """
        try:
            from APIs.canva import create_design
            from APIs.canva import list_designs
            from APIs.canva import get_design
            from APIs.canva import get_design_pages
            from APIs.canva import create_folder
            from APIs.canva import list_folder_items
            from APIs.canva import get_folder
            from APIs.canva import update_folder
            from APIs.canva import delete_folder
            from APIs.canva import create_asset_upload_job
            from APIs.canva import get_asset_upload_job
            from APIs.canva import get_asset
            from APIs.canva import update_asset
            from APIs.canva import delete_asset
            from APIs.canva import create_autofill_job
            from APIs.canva import get_autofill_job
            from APIs.canva import create_comment_thread
            from APIs.canva import create_comment_reply
            from APIs.canva import get_comment_thread
            from APIs.canva import get_comment_reply
            from APIs.canva import list_comment_replies
            from APIs.canva import create_design_import_job
            from APIs.canva import get_design_import_job
            from APIs.canva import create_url_design_import_job
            from APIs.canva import get_url_design_import_job
            from APIs.canva import get_current_user
            from APIs.canva import get_current_user_profile
            from APIs.canva import create_design_export_job
            from APIs.canva import get_design_export_job
             
        except ImportError as e:
            self.fail(f"Failed to import public functions: {e}")

    def test_import_function_callable(self):
        """
        Test that the public functions can be called successfully.
        """
        try:
            from APIs.canva  import create_design
            from APIs.canva import list_designs
            from APIs.canva import get_design
            from APIs.canva import get_design_pages
            from APIs.canva import create_folder
            from APIs.canva import list_folder_items
            from APIs.canva import get_folder
            from APIs.canva import update_folder
            from APIs.canva import delete_folder
            from APIs.canva import create_asset_upload_job
            from APIs.canva import get_asset_upload_job
            from APIs.canva import get_asset
            from APIs.canva import update_asset
            from APIs.canva import delete_asset
            from APIs.canva import create_autofill_job
            from APIs.canva import get_autofill_job
            from APIs.canva import create_comment_thread
            from APIs.canva import create_comment_reply
            from APIs.canva import get_comment_thread
            from APIs.canva import get_comment_reply
            from APIs.canva import list_comment_replies
            from APIs.canva import create_design_import_job
            from APIs.canva import get_design_import_job
            from APIs.canva import create_url_design_import_job
            from APIs.canva import get_url_design_import_job
            from APIs.canva import get_current_user
            from APIs.canva import get_current_user_profile
            from APIs.canva import create_design_export_job
            from APIs.canva import get_design_export_job


            assert callable(create_design)
            assert callable(list_designs)
            assert callable(get_design)
            assert callable(get_design_pages)
            assert callable(create_folder)
            assert callable(list_folder_items)
            assert callable(get_folder)
            assert callable(update_folder)
            assert callable(delete_folder)
            assert callable(create_asset_upload_job)
            assert callable(get_asset_upload_job)
            assert callable(get_asset)
            assert callable(update_asset)
            assert callable(delete_asset)
            assert callable(create_autofill_job)
            assert callable(get_autofill_job)
            assert callable(create_comment_thread)
            assert callable(create_comment_reply)
            assert callable(get_comment_thread)
            assert callable(get_comment_reply)
            assert callable(list_comment_replies)
            assert callable(create_design_import_job)
            assert callable(get_design_import_job)
            assert callable(create_url_design_import_job)
            assert callable(get_url_design_import_job)
            assert callable(get_current_user)
            assert callable(get_current_user_profile)
            assert callable(create_design_export_job)
            assert callable(get_design_export_job)
            
            
        except Exception as e:
            self.fail(f"Failed to import function: {e}")

    def test_import_simulation_engine_modules(self):
        """
        Test that the simulation engine can be imported successfully.
        """
        try:
            importlib.import_module("canva.SimulationEngine.models")
            importlib.import_module("canva.SimulationEngine.db")
            importlib.import_module("canva.SimulationEngine.custom_errors")
            importlib.import_module("canva.SimulationEngine.utils")
        except Exception as e:
            self.fail(f"Failed to import simulation engine: {e}")
    

    def test_simulation_engine_module_usability(self):
        """
        Test that the simulation engine modules can be used successfully.
        """
        try:
            from canva.SimulationEngine.models import DesignTypeInputModel
            from canva.SimulationEngine.db import DB, save_state, load_state
            from canva.SimulationEngine.custom_errors import InvalidDesignIDError
            from canva.SimulationEngine.custom_errors import InvalidAssetIDError
            from canva.SimulationEngine.custom_errors import InvalidTitleError
            from canva.SimulationEngine.custom_errors import InvalidQueryError
            from canva.SimulationEngine.custom_errors import InvalidOwnershipError
            from canva.SimulationEngine.custom_errors import InvalidSortByError

            assert type(DB) == dict
            assert issubclass(DesignTypeInputModel, BaseModel)
            assert issubclass(InvalidDesignIDError, Exception)
            assert issubclass(InvalidAssetIDError, Exception)
            assert issubclass(InvalidTitleError, Exception)
            assert issubclass(InvalidQueryError, Exception)
            assert issubclass(InvalidOwnershipError, Exception)
            assert issubclass(InvalidSortByError, Exception)

            assert callable(save_state)
            assert callable(load_state)

        except Exception as e:
            self.fail(f"Failed to import simulation engine: {e}")
    
    def test_function_map_exists(self):
        """Test that the function map is available."""
        self.assertIsNotNone(_function_map)
        self.assertIsInstance(_function_map, dict)
    
    def test_function_map_contains_functions(self):
        """Test that the function map contains expected functions."""
        expected_functions = [
            'create_design',
            'list_designs',
            'get_design',
            'create_folder',
            'get_current_user'
        ]
        for func_name in expected_functions:
            self.assertIn(func_name, _function_map)
    
    def test_db_module_import(self):
        """Test that DB module is imported correctly."""
        from ..SimulationEngine.db import DB
        self.assertIsInstance(DB, dict)
    
    def test_models_module_has_classes(self):
        """Test that models module contains expected classes."""
        from ..SimulationEngine.models import (
            DesignTypeInputModel,
            DesignModel,
            UserModel,
            AssetModel,
            FolderModel,
            BrandTemplateModel
        )
        
        self.assertTrue(issubclass(DesignTypeInputModel, BaseModel))
        self.assertTrue(issubclass(DesignModel, BaseModel))
        self.assertTrue(issubclass(UserModel, BaseModel))
        self.assertTrue(issubclass(AssetModel, BaseModel))
        self.assertTrue(issubclass(FolderModel, BaseModel))
        self.assertTrue(issubclass(BrandTemplateModel, BaseModel))
    
    def test_custom_errors_import(self):
        """Test that all custom errors can be imported."""
        from ..SimulationEngine.custom_errors import (
            InvalidDesignIDError,
            InvalidAssetIDError,
            InvalidTitleError,
            InvalidQueryError,
            InvalidOwnershipError,
            InvalidSortByError
        )
        
        self.assertTrue(issubclass(InvalidDesignIDError, Exception))
        self.assertTrue(issubclass(InvalidAssetIDError, Exception))
        self.assertTrue(issubclass(InvalidTitleError, Exception))
        self.assertTrue(issubclass(InvalidQueryError, Exception))
        self.assertTrue(issubclass(InvalidOwnershipError, Exception))
        self.assertTrue(issubclass(InvalidSortByError, Exception))
    
    def test_utils_module_import(self):
        """Test that utils module can be imported."""
        from ..SimulationEngine import utils
        self.assertIsNotNone(utils)
    
    def test_get_design_has_correct_signature(self):
        """Test that get_design has the expected signature."""
        from .. import get_design
        sig = typing.get_type_hints(get_design)
        self.assertIsNotNone(sig)
    
    def test_imported_functions_have_docstrings(self):
        """Test that imported functions have docstrings."""
        from APIs.canva import (
            create_design,
            list_designs,
            get_design,
            create_folder
        )
        
        self.assertIsNotNone(create_design.__doc__)
        self.assertIsNotNone(list_designs.__doc__)
        self.assertIsNotNone(get_design.__doc__)
        self.assertIsNotNone(create_folder.__doc__)
    
    def test_job_related_functions_import(self):
        """Test that all job-related functions can be imported."""
        from APIs.canva import (
            create_asset_upload_job,
            get_asset_upload_job,
            create_autofill_job,
            get_autofill_job,
            create_design_import_job,
            get_design_import_job,
            create_url_design_import_job,
            get_url_design_import_job,
            create_design_export_job,
            get_design_export_job
        )
        
        self.assertTrue(callable(create_asset_upload_job))
        self.assertTrue(callable(get_asset_upload_job))
        self.assertTrue(callable(create_autofill_job))
        self.assertTrue(callable(get_autofill_job))
        self.assertTrue(callable(create_design_import_job))
        self.assertTrue(callable(get_design_import_job))
        self.assertTrue(callable(create_url_design_import_job))
        self.assertTrue(callable(get_url_design_import_job))
        self.assertTrue(callable(create_design_export_job))
        self.assertTrue(callable(get_design_export_job))
    
    def test_comment_related_functions_import(self):
        """Test that all comment-related functions can be imported."""
        from APIs.canva import (
            create_comment_thread,
            create_comment_reply,
            get_comment_thread,
            get_comment_reply,
            list_comment_replies
        )
        
        self.assertTrue(callable(create_comment_thread))
        self.assertTrue(callable(create_comment_reply))
        self.assertTrue(callable(get_comment_thread))
        self.assertTrue(callable(get_comment_reply))
        self.assertTrue(callable(list_comment_replies))
    
    def test_asset_functions_import(self):
        """Test that asset-related functions can be imported."""
        from APIs.canva import (
            get_asset,
            update_asset,
            delete_asset
        )
        
        self.assertTrue(callable(get_asset))
        self.assertTrue(callable(update_asset))
        self.assertTrue(callable(delete_asset))
    
    def test_folder_functions_import(self):
        """Test that folder-related functions can be imported."""
        from APIs.canva import (
            create_folder,
            list_folder_items,
            get_folder,
            update_folder,
            delete_folder
        )
        
        self.assertTrue(callable(create_folder))
        self.assertTrue(callable(list_folder_items))
        self.assertTrue(callable(get_folder))
        self.assertTrue(callable(update_folder))
        self.assertTrue(callable(delete_folder))
    
    def test_user_functions_import(self):
        """Test that user-related functions can be imported."""
        from APIs.canva import (
            get_current_user,
            get_current_user_profile
        )
        
        self.assertTrue(callable(get_current_user))
        self.assertTrue(callable(get_current_user_profile))
    
    def test_design_functions_import(self):
        """Test that design-related functions can be imported."""
        from APIs.canva import (
            create_design,
            list_designs,
            get_design,
            get_design_pages
        )
        
        self.assertTrue(callable(create_design))
        self.assertTrue(callable(list_designs))
        self.assertTrue(callable(get_design))
        self.assertTrue(callable(get_design_pages))

if __name__ == '__main__':
    unittest.main()