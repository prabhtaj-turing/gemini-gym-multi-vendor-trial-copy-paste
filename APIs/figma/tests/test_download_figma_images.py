# figma/tests/test_download_figma_images.py

import unittest
import os
import tempfile
import shutil
import pathlib
from unittest.mock import patch

from figma import download_figma_images
from figma import DB
from figma.SimulationEngine.custom_errors import NotFoundError, InvalidInputError, DownloadError
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Mock implementations for utils functions
# These are used as side_effects for patched utils functions.
def mock_get_file_by_key(db_dict, key):
    files = db_dict.get('files', [])
    for f_obj in files:
        if f_obj.get('fileKey') == key:
            return f_obj
    return None

def mock_find_node_by_id(nodes_list, target_id):
    if nodes_list is None: # Ensure nodes_list is not None before iterating
        return None
    for node in nodes_list:
        if node.get('id') == target_id:
            return node
        children = node.get('children')
        if children: # Check if children exist and is iterable
            found_in_child = mock_find_node_by_id(children, target_id)
            if found_in_child:
                return found_in_child
    return None

class TestDownloadFigmaImages(BaseTestCaseWithErrorHandler):

    def setUp(self):
        DB.clear() # Clear the actual figma.DB dictionary

        self.temp_dir_obj = pathlib.Path(tempfile.mkdtemp())
        self.test_dir = str(self.temp_dir_obj) # Destination for downloads

        self.mock_source_files_root = pathlib.Path("./files")

        self.file_key_1 = "file_key_exists_123"
        self.node_id_1 = "node_1_rect_exportable"
        self.node_id_2 = "node_2_ellipse_exportable"
        self.node_id_non_exportable_type = "node_3_group_non_exportable"
        self.node_id_missing_export_settings = "node_4_rect_no_export_settings"
        self.node_id_for_missing_source_file = "node_5_missing_source" # For testing missing source

        # Populate figma.DB
        DB['files'] = [
            {
                "fileKey": self.file_key_1,
                "name": "Test File Alpha",
                "lastModified": "2023-10-26T10:00:00Z",
                "thumbnailUrl": "https://example.com/thumb.png",
                "version": "123",
                "role": "owner",
                "editorType": "figma",
                "linkAccess": "view",
                "schemaVersion": 0,
                "document": {
                    "id": "doc-id-001",
                    "name": "Main Document",
                    "type": "DOCUMENT",
                    "scrollBehavior": "SCROLLS",
                    "children": [
                        {
                            "id": "canvas-id-page1",
                            "name": "Page 1",
                            "type": "CANVAS",
                            "scrollBehavior": "SCROLLS",
                            "backgroundColor": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
                            "children": [
                                {
                                    "id": self.node_id_1, "name": "Exportable Rectangle", "type": "RECTANGLE",
                                    "visible": True, "absoluteBoundingBox": {"x": 10, "y": 20, "width": 100, "height": 50},
                                    "exportSettings": [{"format": "PNG", "suffix": "_rect"}],
                                    "fills": [{"type": "SOLID", "color": {"r":0.5,"g":0.5,"b":0.5,"a":1.0}, "visible": True}]
                                },
                                {
                                    "id": self.node_id_2, "name": "Exportable Ellipse", "type": "ELLIPSE",
                                    "visible": True, "absoluteBoundingBox": {"x": 150, "y": 20, "width": 80, "height": 80},
                                    "exportSettings": [{"format": "JPG", "suffix": "_ellipse", "constraint": {"type": "SCALE", "value": 2.0}}],
                                    "fills": [{"type": "SOLID", "color": {"r":0.2,"g":0.8,"b":0.3,"a":1.0}, "visible": True}]
                                },
                                {
                                    "id": self.node_id_non_exportable_type, "name": "Non-Exportable Group", "type": "GROUP",
                                    "visible": True, "absoluteBoundingBox": {"x": 300, "y": 20, "width": 120, "height": 120},
                                    "children": [],
                                },
                                {
                                    "id": self.node_id_missing_export_settings, "name": "Rectangle Missing Export Settings", "type": "RECTANGLE",
                                    "visible": True, "absoluteBoundingBox": {"x": 10, "y": 200, "width": 100, "height": 50},
                                    "exportSettings": [],
                                    "fills": [{"type": "SOLID", "color": {"r":0.1,"g":0.1,"b":0.1,"a":1.0}, "visible": True}]
                                },
                                { # Node for testing missing source file scenario
                                    "id": self.node_id_for_missing_source_file, "name": "Node With Missing Source File", "type": "FRAME",
                                    "visible": True, "absoluteBoundingBox": {"x": 10, "y": 300, "width": 50, "height": 50}
                                }
                            ]
                        }
                    ]
                },
                "components": {}, "componentSets": {},
                "globalVars": {"styles": {}, "variables": {}, "variableCollections": {}}
            }
        ]

    def tearDown(self):
        shutil.rmtree(self.temp_dir_obj)
        DB.clear()

    @patch('figma.utils.find_node_by_id', side_effect=mock_find_node_by_id)
    @patch('figma.utils.get_file_by_key', side_effect=mock_get_file_by_key)
    @patch('shutil.copy2')
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.is_dir')
    @patch('os.access')
    def test_download_single_image_success_path_exists(self, mock_os_access, mock_path_is_dir, mock_path_mkdir,
                                                      mock_source_is_file, mock_shutil_copy2,
                                                      mock_util_get_file, mock_util_find_node):
        mock_path_is_dir.return_value = True
        mock_os_access.return_value = True

        nodes_to_download = [{"node_id": self.node_id_1, "file_name": "image1.png"}]
        
        p_local_path = pathlib.Path(self.test_dir)
        output_file_name = "image1.png"
        expected_destination_path = p_local_path.joinpath(output_file_name).resolve()
        
        assumed_source_filename = f"{self.node_id_1}.png"
        expected_source_path = self.mock_source_files_root.joinpath(assumed_source_filename)

        status, path = download_figma_images(self.file_key_1, nodes_to_download, self.test_dir)

        self.assertEqual(path, self.test_dir)
        self.assertEqual(status, f"Successfully processed 1 image(s) and saved to '{self.test_dir}'. Paths: {str(expected_destination_path)}")
        
        self.assertEqual(mock_path_mkdir.call_count, 2) 
        mock_path_mkdir.assert_any_call(parents=True, exist_ok=True)
        
        mock_path_is_dir.assert_called_once() 
        mock_os_access.assert_called_once_with(self.test_dir, os.W_OK)
        
        mock_shutil_copy2.assert_called_once_with(expected_source_path, expected_destination_path)
        
        # Check that Path(expected_source_path).is_file() was called.
        # The mock_source_is_file is a general mock for pathlib.Path.is_file.
        # It will be called for the source file check.
        self.assertGreaterEqual(mock_source_is_file.call_count, 1) 
        
        mock_util_get_file.assert_called_once_with(DB, self.file_key_1)
        # Find node will be called with search_roots from the DB and the node_id
        figma_file_obj = mock_get_file_by_key(DB, self.file_key_1) # Get what find_node would use
        search_roots = figma_file_obj["document"]["children"]
        mock_util_find_node.assert_called_once_with(search_roots, self.node_id_1)


    @patch('shutil.copy2')
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.is_dir')
    @patch('os.access')
    def test_download_single_image_success_create_path(self, mock_os_access, mock_path_is_dir, mock_path_mkdir,
                                                       mock_source_is_file, mock_shutil_copy2):
        mock_path_is_dir.return_value = True 
        mock_os_access.return_value = True   

        nodes_to_download = [{"node_id": self.node_id_1, "file_name": "image_created_path.png"}]
        
        p_local_path = pathlib.Path(self.test_dir)
        output_file_name = "image_created_path.png"
        expected_destination_path = p_local_path.joinpath(output_file_name).resolve()
        
        assumed_source_filename = f"{self.node_id_1}.png"
        expected_source_path = self.mock_source_files_root.joinpath(assumed_source_filename)

        status, path = download_figma_images(self.file_key_1, nodes_to_download, self.test_dir)

        self.assertEqual(path, self.test_dir)
        self.assertEqual(status, f"Successfully processed 1 image(s) and saved to '{self.test_dir}'. Paths: {str(expected_destination_path)}")

        self.assertEqual(mock_path_mkdir.call_count, 2)
        mock_path_mkdir.assert_any_call(parents=True, exist_ok=True)

        mock_path_is_dir.assert_called_once()
        mock_os_access.assert_called_once_with(self.test_dir, os.W_OK)
        mock_shutil_copy2.assert_called_once_with(expected_source_path, expected_destination_path)
        self.assertGreaterEqual(mock_source_is_file.call_count, 1)


    @patch('figma.utils.find_node_by_id', side_effect=mock_find_node_by_id)
    @patch('figma.utils.get_file_by_key', side_effect=mock_get_file_by_key)
    @patch('shutil.copy2')
    @patch('pathlib.Path.is_file', return_value=True) 
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.is_dir')
    @patch('os.access')
    def test_download_multiple_images_success(self, mock_os_access, mock_path_is_dir, mock_path_mkdir,
                                             mock_source_is_file, mock_shutil_copy2,
                                             mock_util_get_file, mock_util_find_node):
        mock_path_is_dir.return_value = True
        mock_os_access.return_value = True

        nodes_to_download = [
            {"node_id": self.node_id_1, "file_name": "img_A.png"},
            {"node_id": self.node_id_2, "file_name": "img_B.jpg"}
        ]
        
        p_local_path = pathlib.Path(self.test_dir)
        dest_path1 = p_local_path.joinpath("img_A.png").resolve()
        dest_path2 = p_local_path.joinpath("img_B.jpg").resolve()

        source_path1 = self.mock_source_files_root.joinpath(f"{self.node_id_1}.png")
        source_path2 = self.mock_source_files_root.joinpath(f"{self.node_id_2}.png")

        status, path_str = download_figma_images(self.file_key_1, nodes_to_download, self.test_dir)

        self.assertEqual(path_str, self.test_dir)
        
        self.assertTrue(status.startswith(f"Successfully processed 2 image(s) and saved to '{self.test_dir}'."))
        downloaded_paths_str_part = status.split("Paths: ", 1)[1]
        downloaded_paths_list = sorted([p.strip() for p in downloaded_paths_str_part.split(",")])
        expected_paths_list = sorted([str(dest_path1), str(dest_path2)])
        self.assertEqual(downloaded_paths_list, expected_paths_list)

        self.assertEqual(mock_path_mkdir.call_count, 3) 
        mock_shutil_copy2.assert_any_call(source_path1, dest_path1)
        mock_shutil_copy2.assert_any_call(source_path2, dest_path2)
        self.assertEqual(mock_shutil_copy2.call_count, 2)
        self.assertEqual(mock_source_is_file.call_count, 2) 
        self.assertEqual(mock_util_find_node.call_count, 2)


    def test_invalid_input_empty_file_key(self):
        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=InvalidInputError,
            expected_message = "file_key must be a non-empty string.",
            file_key="", nodes=[{"node_id": "1", "file_name": "f.png"}], local_path=self.test_dir
        )

    @patch('figma.utils.get_file_by_key', side_effect=mock_get_file_by_key)
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.is_dir')
    @patch('os.access')
    def test_input_nodes_empty_list_handled_gracefully(self, mock_os_access, mock_path_is_dir, mock_path_mkdir, mock_util_get_file):
        mock_path_is_dir.return_value = True
        mock_os_access.return_value = True
        
        status, path = download_figma_images(
            file_key=self.file_key_1, 
            nodes=[], 
            local_path=self.test_dir
        )
        
        self.assertEqual(status, "No nodes specified for processing. 0 images processed.")
        self.assertEqual(path, self.test_dir)
        
        mock_path_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_path_is_dir.assert_called_once()
        mock_os_access.assert_called_once_with(self.test_dir, os.W_OK)
        mock_util_get_file.assert_called_once_with(DB, self.file_key_1)


    def test_invalid_input_nodes_not_list(self):
        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=InvalidInputError,
            expected_message="nodes argument must be a list.",
            file_key=self.file_key_1, nodes="not a list", local_path=self.test_dir
        )

    def test_invalid_input_nodes_item_not_dict(self):
        nodes = [{"node_id": "1", "file_name": "f.png"}, "not_a_dict"]
        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=InvalidInputError,
            expected_message="Item at index 1 in nodes list is not a dictionary.",
            file_key=self.file_key_1, nodes=nodes, local_path=self.test_dir
        )

    def test_invalid_input_nodes_item_missing_node_id(self):
        nodes = [{"file_name": "f.png"}]
        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=InvalidInputError,
            expected_message="Item at index 0 in nodes list must have a non-empty string 'node_id'.",
            file_key=self.file_key_1, nodes=nodes, local_path=self.test_dir
        )

    def test_invalid_input_nodes_item_missing_file_name(self):
        nodes = [{"node_id": "1"}]
        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=InvalidInputError,
            expected_message="Item at index 0 in nodes list must have a non-empty string 'file_name'.",
            file_key=self.file_key_1, nodes=nodes, local_path=self.test_dir
        )

    def test_invalid_input_nodes_item_node_id_not_str(self):
        nodes = [{"node_id": 123, "file_name": "f.png"}]
        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=InvalidInputError,
            expected_message="Item at index 0 in nodes list must have a non-empty string 'node_id'.",
            file_key=self.file_key_1, nodes=nodes, local_path=self.test_dir
        )

    def test_invalid_input_nodes_item_file_name_not_str(self):
        nodes = [{"node_id": "1", "file_name": 123}]
        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=InvalidInputError,
            expected_message="Item at index 0 in nodes list must have a non-empty string 'file_name'.",
            file_key=self.file_key_1, nodes=nodes, local_path=self.test_dir
        )

    def test_invalid_input_file_name_is_absolute(self):
        """Tests InvalidInputError when file_name is an absolute path."""
        absolute_file_path = os.path.abspath("image.png")
        nodes = [{"node_id": self.node_id_1, "file_name": absolute_file_path}]
        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=InvalidInputError,
            expected_message=f"file_name '{absolute_file_path}' (for node '{self.node_id_1}') must be a relative path.",
            file_key=self.file_key_1, nodes=nodes, local_path=self.test_dir
        )

    def test_invalid_input_empty_local_path(self):
        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=InvalidInputError,
            expected_message="local_path must be a non-empty string.",
            file_key=self.file_key_1, nodes=[{"node_id": "1", "file_name": "f.png"}], local_path=""
        )

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('os.access', return_value=False)
    def test_invalid_input_local_path_not_writable(self, mock_os_access, mock_path_is_dir, mock_path_mkdir):
        """Tests InvalidInputError when the local_path is not writable."""
        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=InvalidInputError,
            expected_message=f"Local path '{self.test_dir}' is not writable.",
            file_key=self.file_key_1,
            nodes=[{"node_id": self.node_id_1, "file_name": "image.png"}],
            local_path=self.test_dir
        )
        mock_path_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_path_is_dir.assert_called_once()
        mock_os_access.assert_called_once_with(self.test_dir, os.W_OK)

    @patch('pathlib.Path.mkdir')
    def test_invalid_input_cannot_create_local_path(self, mock_path_mkdir):
        mock_path_mkdir.side_effect = OSError("Permission denied")
        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=InvalidInputError,
            expected_message=f"Failed to create or access local directory '{self.test_dir}': Permission denied",
            file_key=self.file_key_1,
            nodes=[{"node_id": self.node_id_1, "file_name": "image.png"}],
            local_path=self.test_dir
        )

    @patch('figma.utils.get_file_by_key', return_value=None) 
    @patch('pathlib.Path.mkdir') 
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('os.access', return_value=True)
    def test_not_found_invalid_file_key(self, mock_os_access, mock_path_is_dir, mock_path_mkdir, mock_util_get_file):
        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=NotFoundError,
            expected_message="Figma file with key 'non_existent_file_key' not found.",
            file_key="non_existent_file_key",
            nodes=[{"node_id": self.node_id_1, "file_name": "image.png"}],
            local_path=self.test_dir
        )
        mock_util_get_file.assert_called_once_with(DB, "non_existent_file_key")
        mock_path_mkdir.assert_called_once_with(parents=True, exist_ok=True)


    @patch('figma.utils.find_node_by_id', return_value=None) 
    @patch('figma.utils.get_file_by_key', side_effect=mock_get_file_by_key) 
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('os.access', return_value=True)
    def test_not_found_node_id_not_exist(self, mock_os_access, mock_path_is_dir, mock_path_mkdir,
                                         mock_util_get_file, mock_util_find_node):
        nodes_to_test = [{"node_id": "non_existent_node_id_qwerty", "file_name": "image.png"}]
        
        figma_file_obj = mock_get_file_by_key(DB, self.file_key_1)
        search_roots = []
        if figma_file_obj and figma_file_obj.get("document") and figma_file_obj.get("document").get("children"):
            search_roots = figma_file_obj["document"]["children"]

        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=NotFoundError,
            expected_message=f"Node with ID 'non_existent_node_id_qwerty' not found in Figma file '{self.file_key_1}'.",
            file_key=self.file_key_1,
            nodes=nodes_to_test,
            local_path=self.test_dir
        )
        mock_util_get_file.assert_called_once_with(DB, self.file_key_1)
        mock_util_find_node.assert_called_once_with(search_roots, "non_existent_node_id_qwerty")
        mock_path_mkdir.assert_called_once_with(parents=True, exist_ok=True)


    @patch('figma.utils.find_node_by_id', side_effect=mock_find_node_by_id)
    @patch('figma.utils.get_file_by_key', side_effect=mock_get_file_by_key)
    @patch('shutil.copy2') 
    @patch('pathlib.Path.is_file', return_value=False) 
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('os.access', return_value=True)
    def test_download_error_source_file_missing(self, mock_os_access, mock_path_is_dir, mock_path_mkdir,
                                                mock_source_is_file, mock_shutil_copy2,
                                                mock_util_get_file, mock_util_find_node):
        node_id_for_test = self.node_id_for_missing_source_file
        nodes = [{"node_id": node_id_for_test, "file_name": "missing_source.png"}]
        
        expected_source_path_str = str(self.mock_source_files_root.joinpath(f"{node_id_for_test}.png"))

        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=NotFoundError,
            expected_message=(
                f"Source image file '{expected_source_path_str}' (for node_id '{node_id_for_test}') not found."
            ),
            file_key=self.file_key_1,
            nodes=nodes,
            local_path=self.test_dir
        )
        self.assertEqual(mock_path_mkdir.call_count, 2) # For local_path and image parent path
        # is_file should be called once for the source file that's missing
        self.assertGreaterEqual(mock_source_is_file.call_count, 1)
        mock_shutil_copy2.assert_not_called()


    @patch('figma.utils.find_node_by_id', side_effect=mock_find_node_by_id)
    @patch('figma.utils.get_file_by_key', side_effect=mock_get_file_by_key)
    @patch('shutil.copy2') 
    @patch('pathlib.Path.is_file', return_value=False) 
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('os.access', return_value=True)
    def test_not_found_multiple_source_files_missing(self, mock_os_access, mock_path_is_dir, mock_path_mkdir,
                                                     mock_source_is_file, mock_shutil_copy2,
                                                     mock_util_get_file, mock_util_find_node):
        # Test case where multiple source files are missing
        # Use existing node IDs that are valid in the mock data
        node_id_1 = self.node_id_1
        node_id_2 = self.node_id_2
        nodes = [
            {"node_id": node_id_1, "file_name": "missing_source_1.png"},
            {"node_id": node_id_2, "file_name": "missing_source_2.png"}
        ]
        
        expected_source_path_1 = str(self.mock_source_files_root.joinpath(f"{node_id_1}.png"))
        expected_source_path_2 = str(self.mock_source_files_root.joinpath(f"{node_id_2}.png"))

        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=NotFoundError,
            expected_message=(
                f"Multiple source image files not found: "
                f"Source image file '{expected_source_path_1}' (for node_id '{node_id_1}') not found.; "
                f"Source image file '{expected_source_path_2}' (for node_id '{node_id_2}') not found."
            ),
            file_key=self.file_key_1,
            nodes=nodes,
            local_path=self.test_dir
        )
        self.assertEqual(mock_path_mkdir.call_count, 3) # For local_path and 2 image parent paths
        # is_file should be called twice for the two source files that are missing
        self.assertEqual(mock_source_is_file.call_count, 2)
        mock_shutil_copy2.assert_not_called()


    @patch('figma.utils.find_node_by_id', side_effect=mock_find_node_by_id)
    @patch('figma.utils.get_file_by_key', side_effect=mock_get_file_by_key)
    @patch('shutil.copy2', side_effect=OSError("Simulated copy error"))
    @patch('pathlib.Path.is_file', return_value=True) 
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('os.access', return_value=True)
    def test_download_error_when_copy_fails_for_a_node(self, mock_os_access, mock_path_is_dir, mock_path_mkdir,
                                                         mock_source_is_file, mock_shutil_copy2,
                                                         mock_util_get_file, mock_util_find_node):
        node_id_to_test = self.node_id_1 
        output_file_name = "generic_copy_fail.png"
        nodes = [{"node_id": node_id_to_test, "file_name": output_file_name}]
        
        p_local_path = pathlib.Path(self.test_dir)
        expected_dest_path = p_local_path.joinpath(output_file_name).resolve()
        expected_source_path = self.mock_source_files_root.joinpath(f"{node_id_to_test}.png")

        self.assert_error_behavior(
            func_to_call=download_figma_images,
            expected_exception_type=DownloadError,
            expected_message=(
                "One or more errors occurred during image processing: "
                f"Failed to copy image for node '{node_id_to_test}' "
                f"(source: '{str(expected_source_path)}', dest: '{str(expected_dest_path)}'): "
                "Simulated copy error"
            ),
            file_key=self.file_key_1,
            nodes=nodes,
            local_path=self.test_dir
        )
        self.assertEqual(mock_path_mkdir.call_count, 2)
        self.assertGreaterEqual(mock_source_is_file.call_count, 1)
        mock_shutil_copy2.assert_called_once_with(expected_source_path, expected_dest_path)

if __name__ == '__main__':
    unittest.main()