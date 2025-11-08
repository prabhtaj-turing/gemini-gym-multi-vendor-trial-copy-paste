import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

class ImportTest(unittest.TestCase):
    def test_import_figma_package(self):
        """Test that the main figma package can be imported."""
        try:
            import APIs.figma
        except ImportError:
            self.fail("Failed to import APIs.figma package")

    def test_import_public_functions(self):
        """Test that public functions can be imported from the figma module."""
        try:
            from APIs.figma.annotation_operations import get_annotations, set_annotation
            from APIs.figma.document_context import get_styles, get_local_components
            from APIs.figma.file_management import get_figma_data, download_figma_images, set_current_file
            from APIs.figma.layout_operations import set_layout_mode
            from APIs.figma.node_creation import create_rectangle, clone_node, create_frame, create_text
            from APIs.figma.node_editing import move_node, resize_node, delete_node, set_fill_color, delete_multiple_nodes, set_text_content, set_stroke_color
            from APIs.figma.node_reading import get_node_info, get_selection, scan_nodes_by_types
        except ImportError as e:
            self.fail(f"Failed to import public functions: {e}")

    def test_public_functions_are_callable(self):
        """Test that the public functions are callable."""
        from APIs.figma.annotation_operations import get_annotations, set_annotation
        from APIs.figma.document_context import get_styles, get_local_components
        from APIs.figma.file_management import get_figma_data, download_figma_images, set_current_file
        from APIs.figma.layout_operations import set_layout_mode
        from APIs.figma.node_creation import create_rectangle, clone_node, create_frame, create_text
        from APIs.figma.node_editing import move_node, resize_node, delete_node, set_fill_color, delete_multiple_nodes, set_text_content, set_stroke_color
        from APIs.figma.node_reading import get_node_info, get_selection, scan_nodes_by_types

        self.assertTrue(callable(get_annotations))
        self.assertTrue(callable(set_annotation))
        self.assertTrue(callable(get_styles))
        self.assertTrue(callable(get_local_components))
        self.assertTrue(callable(get_figma_data))
        self.assertTrue(callable(download_figma_images))
        self.assertTrue(callable(set_current_file))
        self.assertTrue(callable(set_layout_mode))
        self.assertTrue(callable(create_rectangle))
        self.assertTrue(callable(clone_node))
        self.assertTrue(callable(create_frame))
        self.assertTrue(callable(create_text))
        self.assertTrue(callable(move_node))
        self.assertTrue(callable(resize_node))
        self.assertTrue(callable(delete_node))
        self.assertTrue(callable(set_fill_color))
        self.assertTrue(callable(delete_multiple_nodes))
        self.assertTrue(callable(set_text_content))
        self.assertTrue(callable(set_stroke_color))
        self.assertTrue(callable(get_node_info))
        self.assertTrue(callable(get_selection))
        self.assertTrue(callable(scan_nodes_by_types))

    def test_import_simulation_engine_components(self):
        """Test that components from SimulationEngine can be imported."""
        try:
            from APIs.figma.SimulationEngine import utils
            from APIs.figma.SimulationEngine.custom_errors import NodeNotFoundError
            from APIs.figma.SimulationEngine.db import DB
            from APIs.figma.SimulationEngine.models import Node
        except ImportError as e:
            self.fail(f"Failed to import SimulationEngine components: {e}")

    def test_simulation_engine_components_are_usable(self):
        """Test that imported SimulationEngine components are usable."""
        from APIs.figma.SimulationEngine import utils
        from APIs.figma.SimulationEngine.custom_errors import NodeNotFoundError
        from APIs.figma.SimulationEngine.db import DB
        from APIs.figma.SimulationEngine.models import Node

        self.assertTrue(hasattr(utils, 'get_current_file'))
        self.assertTrue(issubclass(NodeNotFoundError, Exception))
        self.assertIsInstance(DB, dict)
        self.assertTrue(hasattr(Node, 'model_validate'))


if __name__ == '__main__':
    unittest.main()
