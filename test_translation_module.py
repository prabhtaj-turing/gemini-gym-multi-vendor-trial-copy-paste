
import json
import pytest
from Scripts.translation_module import translate_and_save

# Helper function to load a DB from the main DBs directory
def load_original_db(name):
    with open(f"DBs/{name}", "r") as f:
        return json.load(f)

@pytest.fixture
def cursor_db_content():
    return load_original_db("CursorDefaultDB.json")

@pytest.fixture
def gemini_db_content():
    return load_original_db("GeminiCliDefaultDB.json")

@pytest.fixture
def copilot_db_content():
    return load_original_db("CopilotDefaultDB.json")

@pytest.fixture
def terminal_db_content():
    return load_original_db("TerminalDefaultDB.json")

def run_test_translation(tmp_path, source_name, source_content, target_name, target_format):
    # Create temporary source and target files
    source_file = tmp_path / f"{source_name}.json"
    target_file = tmp_path / f"{target_name}.json"
    source_file.write_text(json.dumps(source_content))

    # Run the translation
    translate_and_save(str(source_file), str(target_file), source_name, target_format)

    # Read the result from the target file
    with open(target_file, "r") as f:
        return json.load(f)

def test_cursor_to_gemini(tmp_path, cursor_db_content):
    translated = run_test_translation(tmp_path, "cursor", cursor_db_content, "gemini", "gemini")
    assert "git_blame" not in translated["file_system"]["/home/user/project/src/utils.py"]
    assert "knowledge_base" not in translated
    assert translated["tool_metrics"] == {}
    assert "_created" in translated

def test_cursor_to_copilot(tmp_path, cursor_db_content):
    translated = run_test_translation(tmp_path, "cursor", cursor_db_content, "copilot", "copilot")
    assert "knowledge_base" not in translated
    assert "last_edit_params" not in translated

def test_gemini_to_cursor(tmp_path, gemini_db_content):
    translated = run_test_translation(tmp_path, "gemini", gemini_db_content, "cursor", "cursor")
    assert "tool_metrics" not in translated
    assert translated["knowledge_base"] == {}
    assert translated["_next_knowledge_id"] == 1

def test_gemini_to_copilot(tmp_path, gemini_db_content):
    translated = run_test_translation(tmp_path, "gemini", gemini_db_content, "copilot", "copilot")
    assert "tool_metrics" not in translated
    assert "_created" not in translated
    assert translated["_next_pid"] == 1

def test_copilot_to_cursor(tmp_path, copilot_db_content):
    translated = run_test_translation(tmp_path, "copilot", copilot_db_content, "cursor", "cursor")
    assert translated["knowledge_base"] == {}
    assert translated["last_edit_params"] is None

def test_copilot_to_gemini(tmp_path, copilot_db_content):
    translated = run_test_translation(tmp_path, "copilot", copilot_db_content, "gemini", "gemini")
    assert "_next_pid" not in translated
    assert translated["tool_metrics"] == {}
    assert "_created" in translated

def test_terminal_to_cursor(tmp_path, terminal_db_content):
    translated = run_test_translation(tmp_path, "terminal", terminal_db_content, "cursor", "cursor")
    assert "metadata" not in list(translated["file_system"].values())[0]
    assert translated["knowledge_base"] == {}

def test_cursor_to_terminal(tmp_path, cursor_db_content):
    translated = run_test_translation(tmp_path, "cursor", cursor_db_content, "terminal", "terminal")
    assert "metadata" in list(translated["file_system"].values())[0]
    assert "environment" in translated

def test_terminal_to_gemini(tmp_path, terminal_db_content):
    translated = run_test_translation(tmp_path, "terminal", terminal_db_content, "gemini", "gemini")
    assert "metadata" not in list(translated["file_system"].values())[0]
    assert translated["tool_metrics"] == {}

def test_gemini_to_terminal(tmp_path, gemini_db_content):
    translated = run_test_translation(tmp_path, "gemini", gemini_db_content, "terminal", "terminal")
    assert "metadata" in list(translated["file_system"].values())[0]
    assert "tool_metrics" not in translated

def test_terminal_to_copilot(tmp_path, terminal_db_content):
    translated = run_test_translation(tmp_path, "terminal", terminal_db_content, "copilot", "copilot")
    assert "metadata" not in list(translated["file_system"].values())[0]
    assert "environment" not in translated

def test_copilot_to_terminal(tmp_path, copilot_db_content):
    translated = run_test_translation(tmp_path, "copilot", copilot_db_content, "terminal", "terminal")
    assert "metadata" in list(translated["file_system"].values())[0]
    assert "environment" in translated
