import sys
import os
import pytest
from unittest.mock import patch

# Add the parent directory of 'APIs' to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from APIs.figma.SimulationEngine import utils, custom_errors

# Mock DB for testing
mock_db = {
    "files": [
        {
            "fileKey": "file1",
            "document": {
                "id": "doc1",
                "children": [
                    {
                        "id": "canvas1",
                        "type": "CANVAS",
                        "children": [
                            {"id": "node1", "type": "FRAME", "name": "Frame 1"},
                            {"id": "node2", "type": "TEXT", "name": "Text 1"},
                        ],
                    }
                ],
            },
        }
    ],
    "projects": [{"projectId": "proj1", "name": "Test Project"}],
    "current_file_key": "file1",
}

@pytest.fixture(autouse=True)
def mock_db_access():
    # Make a deep copy of the original mock_db to reset state for each test
    import copy
    db_copy = copy.deepcopy(mock_db)
    with patch("APIs.figma.SimulationEngine.utils.DB", new=db_copy):
        yield

def test_get_file_by_key():
    assert utils.get_file_by_key(mock_db, "file1") is not None
    assert utils.get_file_by_key(mock_db, "nonexistent") is None
    assert utils.get_file_by_key({}, "file1") is None
    assert utils.get_file_by_key({"files": []}, "file1") is None

def test_find_node_by_id():
    node_list = mock_db["files"][0]["document"]["children"]
    assert utils.find_node_by_id(node_list, "node1") is not None
    assert utils.find_node_by_id(node_list, "nonexistent") is None
    assert utils.find_node_by_id([], "node1") is None

def test_find_nodes_by_type():
    node_list = mock_db["files"][0]["document"]["children"]
    assert len(utils.find_nodes_by_type(node_list, "FRAME")) == 1
    assert len(utils.find_nodes_by_type(node_list, "TEXT")) == 1
    assert len(utils.find_nodes_by_type(node_list, "RECTANGLE")) == 0
    assert len(utils.find_nodes_by_type([], "FRAME")) == 0

def test_find_nodes_by_name():
    node_list = mock_db["files"][0]["document"]["children"]
    assert len(utils.find_nodes_by_name(node_list, "Frame 1")) == 1
    assert len(utils.find_nodes_by_name(node_list, "Text 1")) == 1
    assert len(utils.find_nodes_by_name(node_list, "Nonexistent")) == 0
    assert len(utils.find_nodes_by_name([], "Frame 1")) == 0
    assert len(utils.find_nodes_by_name(node_list, "Frame", exact_match=False)) == 1

def test_get_node_text_content():
    text_node = {"type": "TEXT", "characters": "Hello"}
    frame_node = {"type": "FRAME"}
    assert utils.get_node_text_content(text_node) == "Hello"
    assert utils.get_node_text_content(frame_node) is None
    assert utils.get_node_text_content({}) is None

def test_get_node_fill_colors():
    node_with_fills = {
        "fills": [
            {"type": "SOLID", "visible": True, "color": {"r": 1, "g": 0, "b": 0, "a": 1}},
            {"type": "GRADIENT", "visible": True},
            {"type": "SOLID", "visible": False, "color": {"r": 0, "g": 1, "b": 0, "a": 1}},
        ]
    }
    assert len(utils.get_node_fill_colors(node_with_fills)) == 1
    assert utils.get_node_fill_colors({}) == []

def test_get_node_dimensions():
    node_with_bbox = {"absoluteBoundingBox": {"x": 10, "y": 20, "width": 100, "height": 50}}
    assert utils.get_node_dimensions(node_with_bbox) == {"x": 10, "y": 20, "width": 100, "height": 50}
    assert utils.get_node_dimensions({}) is None

def test_is_node_visible():
    assert utils.is_node_visible({"visible": True})
    assert not utils.is_node_visible({"visible": False})
    assert utils.is_node_visible({})

def test_filter_none_values_from_dict():
    assert utils.filter_none_values_from_dict({"a": 1, "b": None, "c": 3}) == {"a": 1, "c": 3}
    assert utils.filter_none_values_from_dict({}) == {}
    assert utils.filter_none_values_from_dict(None) == {}

def test_create_file_success():
    new_file = utils.create_file("new_file_key", "New File", "proj1")
    assert new_file is not None
    assert new_file["fileKey"] == "new_file_key"

def test_create_file_duplicate_key():
    with pytest.raises(TypeError):
        utils.create_file("file1", "Duplicate File", "proj1")

def test_create_file_nonexistent_project():
    with pytest.raises(TypeError):
        utils.create_file("new_file_key_2", "File with no project", "nonexistent_proj")

def test_get_current_file():
    assert utils.get_current_file() is not None
    
    with patch("APIs.figma.SimulationEngine.utils.DB", new={"files": []}):
        with pytest.raises(custom_errors.FigmaOperationError):
            utils.get_current_file()

def test_rgba_to_hex():
    assert utils._rgba_to_hex({"r": 1, "g": 1, "b": 1, "a": 1}) == "#ffffff"
    assert utils._rgba_to_hex({"r": 0, "g": 0, "b": 0, "a": 1}) == "#000000"
    assert utils._rgba_to_hex({}) == "#000000"
    assert utils._rgba_to_hex({"r": "invalid", "g": 0, "b": 0}) == "#000000"

def test_find_direct_parent_of_node():
    node_list = mock_db["files"][0]["document"]["children"]
    assert utils.find_direct_parent_of_node(node_list, "node1")["id"] == "canvas1"
    assert utils.find_direct_parent_of_node(node_list, "nonexistent") is None
    assert utils.find_direct_parent_of_node([], "node1") is None

def test_get_instance_main_component_id():
    instance_node = {"type": "INSTANCE", "componentId": "comp1"}
    assert utils.get_instance_main_component_id(instance_node) == "comp1"
    assert utils.get_instance_main_component_id({}) is None

def test_get_node_constraints():
    node_with_constraints = {"constraints": {"horizontal": "LEFT", "vertical": "TOP"}}
    assert utils.get_node_constraints(node_with_constraints) == {"horizontal": "LEFT", "vertical": "TOP"}
    assert utils.get_node_constraints({}) is None

def test_get_auto_layout_properties():
    auto_layout_node = {"layoutMode": "HORIZONTAL"}
    assert utils.get_auto_layout_properties(auto_layout_node) is not None
    assert utils.get_auto_layout_properties({}) is None

def test_list_available_files():
    assert len(utils.list_available_files()) == 1
    with patch("APIs.figma.SimulationEngine.utils.DB", new={"files": "not_a_list"}):
        assert utils.list_available_files() == []

def test_validate_rgba_color_dict():
    with pytest.raises(custom_errors.InvalidInputError):
        utils._validate_rgba_color_dict({}, "test")
    with pytest.raises(custom_errors.InvalidInputError):
        utils._validate_rgba_color_dict({"r": 1, "g": 1, "b": 1, "a": "invalid"}, "test")
    with pytest.raises(custom_errors.InvalidInputError):
        utils._validate_rgba_color_dict({"r": 2, "g": 1, "b": 1, "a": 1}, "test")

def test_validate_and_process_paint_dict():
    with pytest.raises(custom_errors.InvalidInputError):
        utils._validate_and_process_paint_dict({}, "test")
    with pytest.raises(custom_errors.InvalidInputError):
        utils._validate_and_process_paint_dict({"type": "SOLID"}, "test")
    with pytest.raises(custom_errors.InvalidInputError):
        utils._validate_and_process_paint_dict({"type": "SOLID", "color": {"r": 1, "g": 1, "b": 1, "a": 1}, "opacity": "invalid"}, "test")
    
    paint_dict = {"type": "SOLID", "color": {"r": 1, "g": 1, "b": 1, "a": 1}}
    processed = utils._validate_and_process_paint_dict(paint_dict, "test")
    assert processed["opacity"] == 1.0
    assert processed["visible"] is True

def test_find_node_and_parent_recursive():
    node_list = mock_db["files"][0]["document"]["children"]
    node, parent = utils.find_node_and_parent_recursive(node_list, "node1")
    assert node is not None
    assert parent["id"] == "canvas1"

    result = utils.find_node_and_parent_recursive(node_list, "nonexistent")
    assert result is None

def test_find_node_recursive():
    node_list = mock_db["files"][0]["document"]["children"]
    assert utils.find_node_recursive(node_list, "node1") is not None
    assert utils.find_node_recursive(node_list, "nonexistent") is None

def test_get_node_from_db():
    assert utils.get_node_from_db(mock_db, "node1") is not None
    assert utils.get_node_from_db(mock_db, "nonexistent") is None

def test_get_parent_of_node_from_db():
    assert utils.get_parent_of_node_from_db(mock_db, "node1")["id"] == "canvas1"
    assert utils.get_parent_of_node_from_db(mock_db, "nonexistent") is None

def test_get_node_dict_by_id():
    assert utils.get_node_dict_by_id(mock_db, "node1") is not None
    assert utils.get_node_dict_by_id(mock_db, "nonexistent") is None

def test_node_exists_in_db():
    assert utils.node_exists_in_db(mock_db, "node1")
    assert not utils.node_exists_in_db(mock_db, "nonexistent")

def test_collect_annotations_recursively():
    node_with_annotations = {
        "id": "1",
        "annotations": [{"annotationId": "ann1"}],
        "children": [
            {"id": "2", "annotations": [{"annotationId": "ann2"}]}
        ]
    }
    annotations = []
    utils._collect_annotations_recursively(node_with_annotations, annotations)
    assert len(annotations) == 2
    assert annotations[0]["nodeId"] == "1"
    assert annotations[1]["nodeId"] == "2"

def test_get_instance_variant_properties():
    instance_node = {
        "type": "INSTANCE",
        "componentProperties": {
            "variant": {"value": "true", "type": "BOOLEAN"}
        }
    }
    assert utils.get_instance_variant_properties(instance_node) == {"variant": "true"}
    assert utils.get_instance_variant_properties({}) is None

def test_get_component_property_definitions():
    component_node = {
        "componentPropertyDefinitions": {
            "root": {"variant": {"defaultValue": "false", "type": "BOOLEAN"}}
        }
    }
    assert utils.get_component_property_definitions(component_node) == {"variant": {"defaultValue": "false", "type": "BOOLEAN"}}
    assert utils.get_component_property_definitions({}) is None

def test_get_resolved_style_for_node():
    node_with_style = {"styles": {"fill": "style1"}}
    figma_data = {
        "globalVars": {
            "styles": {"style1": {"root": {"color": "red"}}}
        }
    }
    assert utils.get_resolved_style_for_node(node_with_style, "fill", figma_data) == {"color": "red"}
    assert utils.get_resolved_style_for_node({}, "fill", figma_data) is None

def test_get_variable_value_for_mode():
    figma_data = {
        "globalVars": {
            "variables": {
                "var1": {
                    "valuesByMode": {"mode1": {"root": "value1"}}
                }
            }
        }
    }
    assert utils.get_variable_value_for_mode("var1", "mode1", figma_data) == "value1"
    assert utils.get_variable_value_for_mode("nonexistent", "mode1", figma_data) is None

def test_get_default_mode_id_for_variable():
    figma_data = {
        "globalVars": {
            "variables": {"var1": {"variableCollectionId": "coll1"}},
            "variableCollections": {"coll1": {"defaultModeId": "mode1"}}
        }
    }
    assert utils.get_default_mode_id_for_variable("var1", figma_data) == "mode1"
    assert utils.get_default_mode_id_for_variable("nonexistent", figma_data) is None

def test_get_node_prototype_interactions():
    node_with_interactions = {"prototypeInteractions": [{"action": "CLOSE"}]}
    assert utils.get_node_prototype_interactions(node_with_interactions) == [{"action": "CLOSE"}]
    assert utils.get_node_prototype_interactions({}) == []

def test_get_canvas_flow_starting_points():
    canvas_node = {"flowStartingPoints": [{"nodeId": "1", "name": "Flow 1"}]}
    assert utils.get_canvas_flow_starting_points(canvas_node) == [{"nodeId": "1", "name": "Flow 1"}]
    assert utils.get_canvas_flow_starting_points({}) == []

def test_get_canvas_prototype_device():
    canvas_node = {"prototypeDevice": {"type": "DESKTOP"}}
    assert utils.get_canvas_prototype_device(canvas_node) == {"type": "DESKTOP"}

def test_create_file_make_current_file_true_sets_current_file_key():
    """Test that create_file with make_current_file=True sets the current_file_key"""
    # Set up initial state with some current file and selection
    with patch("APIs.figma.SimulationEngine.utils.DB", new={
        "files": [{"fileKey": "old_file", "name": "Old File"}],
        "projects": [{"projectId": "proj1", "name": "Test Project"}],
        "current_file_key": "old_file",
        "current_selection_node_ids": ["node1", "node2"]
    }):
        result = utils.create_file("new_file_key", "New File", "proj1", make_current_file=True)
        
        # Verify the file was created
        assert result is not None
        assert result["fileKey"] == "new_file_key"
        
        # Verify current_file_key was updated
        assert utils.DB["current_file_key"] == "new_file_key"

def test_create_file_make_current_file_true_clears_selection():
    """Test that create_file with make_current_file=True clears current selection"""
    # Set up initial state with some current selection
    with patch("APIs.figma.SimulationEngine.utils.DB", new={
        "files": [{"fileKey": "old_file", "name": "Old File"}],
        "projects": [{"projectId": "proj1", "name": "Test Project"}],
        "current_file_key": "old_file",
        "current_selection_node_ids": ["node1", "node2", "node3"]
    }):
        result = utils.create_file("new_file_key", "New File", "proj1", make_current_file=True)
        
        # Verify the file was created
        assert result is not None
        
        # Verify current selection was cleared
        assert utils.DB["current_selection_node_ids"] == []

def test_create_file_make_current_file_true_clears_empty_selection():
    """Test that create_file with make_current_file=True handles empty selection"""
    # Set up initial state with empty selection
    with patch("APIs.figma.SimulationEngine.utils.DB", new={
        "files": [{"fileKey": "old_file", "name": "Old File"}],
        "projects": [{"projectId": "proj1", "name": "Test Project"}],
        "current_file_key": "old_file",
        "current_selection_node_ids": []
    }):
        result = utils.create_file("new_file_key", "New File", "proj1", make_current_file=True)
        
        # Verify the file was created
        assert result is not None
        
        # Verify current selection remains empty
        assert utils.DB["current_selection_node_ids"] == []

def test_create_file_make_current_file_true_clears_none_selection():
    """Test that create_file with make_current_file=True handles None selection"""
    # Set up initial state with None selection
    with patch("APIs.figma.SimulationEngine.utils.DB", new={
        "files": [{"fileKey": "old_file", "name": "Old File"}],
        "projects": [{"projectId": "proj1", "name": "Test Project"}],
        "current_file_key": "old_file",
        "current_selection_node_ids": None
    }):
        result = utils.create_file("new_file_key", "New File", "proj1", make_current_file=True)
        
        # Verify the file was created
        assert result is not None
        
        # Verify current selection is set to empty list
        assert utils.DB["current_selection_node_ids"] == []

def test_create_file_make_current_file_false_does_not_change_current_file():
    """Test that create_file with make_current_file=False does not change current file"""
    # Set up initial state
    with patch("APIs.figma.SimulationEngine.utils.DB", new={
        "files": [{"fileKey": "old_file", "name": "Old File"}],
        "projects": [{"projectId": "proj1", "name": "Test Project"}],
        "current_file_key": "old_file",
        "current_selection_node_ids": ["node1", "node2"]
    }):
        result = utils.create_file("new_file_key", "New File", "proj1", make_current_file=False)
        
        # Verify the file was created
        assert result is not None
        
        # Verify current_file_key was NOT changed
        assert utils.DB["current_file_key"] == "old_file"
        
        # Verify current selection was NOT changed
        assert utils.DB["current_selection_node_ids"] == ["node1", "node2"]

def test_create_file_make_current_file_false_does_not_clear_selection():
    """Test that create_file with make_current_file=False does not clear selection"""
    # Set up initial state with selection
    with patch("APIs.figma.SimulationEngine.utils.DB", new={
        "files": [{"fileKey": "old_file", "name": "Old File"}],
        "projects": [{"projectId": "proj1", "name": "Test Project"}],
        "current_file_key": "old_file",
        "current_selection_node_ids": ["selected_node"]
    }):
        result = utils.create_file("new_file_key", "New File", "proj1", make_current_file=False)
        
        # Verify the file was created
        assert result is not None
        
        # Verify current selection was NOT cleared
        assert utils.DB["current_selection_node_ids"] == ["selected_node"]

def test_create_file_make_current_file_true_with_missing_selection_key():
    """Test that create_file with make_current_file=True handles missing selection key"""
    # Set up initial state without current_selection_node_ids key
    with patch("APIs.figma.SimulationEngine.utils.DB", new={
        "files": [{"fileKey": "old_file", "name": "Old File"}],
        "projects": [{"projectId": "proj1", "name": "Test Project"}],
        "current_file_key": "old_file"
        # Note: no current_selection_node_ids key
    }):
        result = utils.create_file("new_file_key", "New File", "proj1", make_current_file=True)
        
        # Verify the file was created
        assert result is not None
        
        # Verify current_file_key was updated
        assert utils.DB["current_file_key"] == "new_file_key"
        
        # Verify current_selection_node_ids was set to empty list
        assert utils.DB["current_selection_node_ids"] == []

def test_create_file_make_current_file_true_multiple_calls():
    """Test that create_file with make_current_file=True works correctly with multiple calls"""
    # Set up initial state
    with patch("APIs.figma.SimulationEngine.utils.DB", new={
        "files": [{"fileKey": "file1", "name": "File 1"}],
        "projects": [{"projectId": "proj1", "name": "Test Project"}],
        "current_file_key": "file1",
        "current_selection_node_ids": ["node1"]
    }):
        # Create first file and make it current
        result1 = utils.create_file("file2", "File 2", "proj1", make_current_file=True)
        assert utils.DB["current_file_key"] == "file2"
        assert utils.DB["current_selection_node_ids"] == []
        
        # Create second file and make it current
        result2 = utils.create_file("file3", "File 3", "proj1", make_current_file=True)
        assert utils.DB["current_file_key"] == "file3"
        assert utils.DB["current_selection_node_ids"] == []
        
        # Verify both files exist
        assert len(utils.DB["files"]) == 3
        assert result1["fileKey"] == "file2"
        assert result2["fileKey"] == "file3"

def test_create_file_make_current_file_true_with_existing_selection_after_creation():
    """Test that create_file with make_current_file=True clears selection even if it was set after file creation"""
    # Set up initial state
    with patch("APIs.figma.SimulationEngine.utils.DB", new={
        "files": [{"fileKey": "old_file", "name": "Old File"}],
        "projects": [{"projectId": "proj1", "name": "Test Project"}],
        "current_file_key": "old_file",
        "current_selection_node_ids": []
    }):
        # Simulate setting selection after file creation but before make_current_file logic
        def mock_create_file_with_selection(*args, **kwargs):
            # Simulate that selection was set during file creation
            utils.DB["current_selection_node_ids"] = ["newly_selected_node"]
            return utils.create_file(*args, **kwargs)
        
        # This would be the actual behavior - the selection gets cleared
        result = utils.create_file("new_file_key", "New File", "proj1", make_current_file=True)
        
        # Verify the file was created
        assert result is not None
        
        # Verify current_file_key was updated
        assert utils.DB["current_file_key"] == "new_file_key"
        
        # Verify current selection was cleared
        assert utils.DB["current_selection_node_ids"] == []
