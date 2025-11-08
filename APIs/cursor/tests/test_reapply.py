# cursor/tests/test_reapply.py
import unittest
import copy
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import function to test and dependencies for patching/setup
from ..cursorAPI import reapply
from ..SimulationEngine import utils # For helpers used in tests
from .. import DB as GlobalDBSource
from ..SimulationEngine.llm_interface import GEMINI_API_KEY_FROM_ENV, call_llm
from ..SimulationEngine.custom_errors import LastEditNotFoundError, LLMGenerationError

# --- Helper to check if API key is available for integration tests ---
GEMINI_API_KEY_IS_AVAILABLE = bool(GEMINI_API_KEY_FROM_ENV)

def normalize_for_db(path_string):
    if path_string is None:
        return None
    # Remove any drive letter prefix first
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    # Then normalize and convert slashes
    return os.path.normpath(path_string).replace("\\", "/")

def minimal_reset_db_for_reapply(workspace_path_for_db=None):
    """Creates a fresh minimal DB state for testing, clearing and setting up root."""
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="test_reapply_workspace_")
    
    # Normalize workspace path
    workspace_path_for_db = normalize_for_db(workspace_path_for_db)
    
    # Initialize common directory to match workspace path
    utils.update_common_directory(workspace_path_for_db)
    
    db_state = {
        "workspace_root": workspace_path_for_db,
        "cwd": workspace_path_for_db,
        "file_system": {},
        "last_edit_params": None,
        "background_processes": {},
        "_next_pid": 1
    }

    # Create root directory entry
    db_state["file_system"][workspace_path_for_db] = {
        "path": workspace_path_for_db,
        "is_directory": True,
        "content_lines": [],
        "size_bytes": 0,
        "last_modified": utils.get_current_timestamp_iso()
    }
    
    return workspace_path_for_db, db_state

# Configure basic logging if needed for debugging test runs
# logging.basicConfig(level=logging.INFO)

# Sample complex code for tests
COMPLEX_PYTHON_SERVICE = '''
# service.py
import logging
import os
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataProcessor:
    """Service class for processing data from various sources."""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path or "config.json")
        self.last_run = None
        self.cache = {}
        
    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if not os.path.exists(path):
                logger.warning(f"Config file {path} not found. Using defaults.")
                return {"default_timeout": 30, "retry_attempts": 3}
                
            with open(path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {"default_timeout": 30, "retry_attempts": 3}
    
    def process_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single data item."""
        if not item_data or not isinstance(item_data, dict):
            logger.error("Invalid item data provided")
            raise ValueError("Item data must be a non-empty dictionary")
            
        item_id = item_data.get('id')
        if not item_id:
            logger.warning("Item missing ID field")
            item_id = f"generated_{datetime.now().timestamp()}"
            item_data['id'] = item_id
        
        # Check cache
        if item_id in self.cache:
            logger.debug(f"Using cached result for item {item_id}")
            return self.cache[item_id]
            
        # Apply transformations
        result = self._transform_data(item_data)
        
        # Update cache
        self.cache[item_id] = result
        self.last_run = datetime.now()
        
        return result
    
    def _transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformation rules to the data."""
        result = data.copy()
        
        # Apply normalization
        if 'name' in result:
            result['name'] = result['name'].strip().title()
            
        # Calculate additional fields
        if 'values' in result and isinstance(result['values'], list):
            result['sum'] = sum(v for v in result['values'] if isinstance(v, (int, float)))
            result['count'] = len(result['values'])
            result['average'] = result['sum'] / result['count'] if result['count'] > 0 else 0
        
        # Apply timestamp
        result['processed_at'] = datetime.now().isoformat()
        
        return result
    
    def process_batch(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of items."""
        if not items:
            logger.warning("Empty batch provided")
            return []
            
        logger.info(f"Processing batch of {len(items)} items")
        results = []
        errors = 0
        
        for item in items:
            try:
                result = self.process_item(item)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                errors += 1
        
        logger.info(f"Batch processing complete. Processed: {len(results)}, Errors: {errors}")
        return results
    
    def clear_cache(self) -> None:
        """Clear the internal cache."""
        cache_size = len(self.cache)
        self.cache = {}
        logger.info(f"Cleared cache of {cache_size} items")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "cache_size": len(self.cache),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "config": self.config
        }
'''

# Sample complex React component for tests
COMPLEX_REACT_COMPONENT = '''
// TaskManager.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Container, 
  Grid, 
  Paper, 
  Typography, 
  Button, 
  List, 
  ListItem, 
  ListItemText,
  IconButton,
  TextField,
  CircularProgress
} from '@material-ui/core';
import { Delete as DeleteIcon, Edit as EditIcon } from '@material-ui/icons';

const API_URL = 'https://api.example.com/tasks';

const TaskManager = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDescription, setNewTaskDescription] = useState('');
  
  // Load tasks on component mount
  useEffect(() => {
    const fetchTasks = async () => {
      setLoading(true);
      try {
        const response = await axios.get(API_URL);
        setTasks(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching tasks:', err);
        setError('Failed to load tasks. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchTasks();
  }, []);
  
  const handleCreateTask = async () => {
    if (!newTaskTitle.trim()) {
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(API_URL, {
        title: newTaskTitle,
        description: newTaskDescription,
        completed: false,
        createdAt: new Date().toISOString()
      });
      
      setTasks([...tasks, response.data]);
      setNewTaskTitle('');
      setNewTaskDescription('');
      setError(null);
    } catch (err) {
      console.error('Error creating task:', err);
      setError('Failed to create task. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleDeleteTask = async (taskId) => {
    setLoading(true);
    try {
      await axios.delete(`${API_URL}/${taskId}`);
      setTasks(tasks.filter(task => task.id !== taskId));
      setError(null);
    } catch (err) {
      console.error('Error deleting task:', err);
      setError('Failed to delete task. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleToggleComplete = async (taskId, currentStatus) => {
    setLoading(true);
    try {
      const response = await axios.patch(`${API_URL}/${taskId}`, {
        completed: !currentStatus
      });
      
      setTasks(tasks.map(task => 
        task.id === taskId ? { ...task, completed: response.data.completed } : task
      ));
      setError(null);
    } catch (err) {
      console.error('Error updating task:', err);
      setError('Failed to update task. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Container maxWidth="md">
      <Typography variant="h4" component="h1" gutterBottom>
        Task Manager
      </Typography>
      
      {error && (
        <Paper elevation={2} style={{ padding: '1rem', marginBottom: '1rem', backgroundColor: '#ffebee' }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      )}
      
      <Paper elevation={3} style={{ padding: '1rem', marginBottom: '2rem' }}>
        <Typography variant="h6" gutterBottom>
          Create New Task
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Task Title"
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
              variant="outlined"
              size="small"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Description"
              value={newTaskDescription}
              onChange={(e) => setNewTaskDescription(e.target.value)}
              variant="outlined"
              size="small"
              multiline
              rows={3}
            />
          </Grid>
          <Grid item xs={12}>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleCreateTask}
              disabled={loading || !newTaskTitle.trim()}
            >
              {loading ? <CircularProgress size={24} /> : 'Create Task'}
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      <Paper elevation={3} style={{ padding: '1rem' }}>
        <Typography variant="h6" gutterBottom>
          Task List
        </Typography>
        
        {loading && tasks.length === 0 ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
            <CircularProgress />
          </div>
        ) : tasks.length === 0 ? (
          <Typography align="center" style={{ padding: '2rem' }}>
            No tasks available. Create your first task above!
          </Typography>
        ) : (
          <List>
            {tasks.map(task => (
              <ListItem key={task.id} divider>
                <ListItemText
                  primary={task.title}
                  secondary={task.description}
                  style={{ textDecoration: task.completed ? 'line-through' : 'none' }}
                />
                <IconButton 
                  edge="end" 
                  aria-label="toggle-complete"
                  onClick={() => handleToggleComplete(task.id, task.completed)}
                >
                  <EditIcon />
                </IconButton>
                <IconButton 
                  edge="end" 
                  aria-label="delete" 
                  onClick={() => handleDeleteTask(task.id)}
                >
                  <DeleteIcon />
                </IconButton>
              </ListItem>
            ))}
          </List>
        )}
      </Paper>
    </Container>
  );
};

export default TaskManager;
'''

class TestReapplyMocked(unittest.TestCase):
    """
    Unit tests for the reapply function, mocking the LLM call
    to verify internal logic like state retrieval, prompt construction,
    and state updates based on a known LLM response.
    """

    def setUp(self):
        """Prepares an isolated database state for each test method."""
        # Create temporary workspace and DB state
        self.workspace_path, self.db_for_test = minimal_reset_db_for_reapply()

        # Patch DB in modules where it's accessed by reapply or its utils
        self.db_patcher_for_init = patch("cursor.DB", self.db_for_test)
        self.db_patcher_for_init.start()
        self.db_patcher_for_utils = patch("cursor.SimulationEngine.utils.DB", self.db_for_test)
        self.db_patcher_for_utils.start()
        # Patch 'DB' in the cursorAPI module where the actual function is defined
        self.db_patcher_for_cursorapi = patch("cursor.cursorAPI.DB", self.db_for_test)
        self.db_patcher_for_cursorapi.start()

        # CRITICAL: Patch 'DB' in the db module where validate_workspace_hydration is defined
        self.db_patcher_for_db_module = patch("cursor.SimulationEngine.db.DB", self.db_for_test)
        self.db_patcher_for_db_module.start()

        # Patch the call_llm function where it's imported in cursorAPI.py
        self.call_llm_patcher = patch('cursor.cursorAPI.call_llm') # Patching where it's actually imported
        self.mock_call_llm = self.call_llm_patcher.start()

    def tearDown(self):
        """Restores original state after each test."""
        self.call_llm_patcher.stop()
        self.db_patcher_for_db_module.stop()
        self.db_patcher_for_cursorapi.stop()
        self.db_patcher_for_utils.stop()
        self.db_patcher_for_init.stop()
        
        # Clean up temporary workspace
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    # --- Test Helper Methods ---
    def _add_dir_to_db(self, path: str, is_abs: bool = False):
        abs_path = path if is_abs else os.path.normpath(os.path.join(self.workspace_path, path))
        if abs_path not in self.db_for_test["file_system"]:
            # Create the directory on filesystem
            os.makedirs(abs_path, exist_ok=True)
            
            self.db_for_test["file_system"][abs_path] = {
                "path": abs_path, 
                "is_directory": True, 
                "content_lines": [], 
                "size_bytes": 0, 
                "last_modified": utils.get_current_timestamp_iso()
            }
        parent_dir = os.path.dirname(abs_path)
        # Simplified recursive parent creation for tests
        if parent_dir and parent_dir != abs_path and parent_dir != self.workspace_path and parent_dir not in self.db_for_test["file_system"] and parent_dir != os.path.dirname(self.workspace_path):
            self._add_dir_to_db(parent_dir, is_abs=True)
        return abs_path

    def _add_file_to_db(self, path: str, content_lines_raw: list[str]):
        abs_path = os.path.normpath(os.path.join(self.workspace_path, path)) # Assume path relative to workspace_path
        dir_name = os.path.dirname(abs_path)
        if dir_name and dir_name != self.workspace_path and dir_name not in self.db_for_test["file_system"]:
            self._add_dir_to_db(dir_name, is_abs=True)
        content_lines = utils._normalize_lines(content_lines_raw, ensure_trailing_newline=True)
        
        # Create the file on filesystem
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(content_lines)
        
        self.db_for_test["file_system"][abs_path] = {
            "path": abs_path, 
            "is_directory": False, 
            "content_lines": content_lines,
            "size_bytes": utils.calculate_size_bytes(content_lines), 
            "last_modified": utils.get_current_timestamp_iso()
        }
        return abs_path

    def _get_file_content_lines(self, path_rel_to_ws_root: str):
        abs_path = os.path.normpath(os.path.join(self.workspace_path, path_rel_to_ws_root))
        entry = self.db_for_test.get("file_system", {}).get(abs_path)
        return entry.get("content_lines", []) if entry and not entry.get("is_directory") else None

    # --- Mocked Test Cases ---

    def test_reapply_success_mocked(self):
        """Verify successful reapply with a mocked LLM providing new content."""
        target_rel = "fix_me.py"
        original_content = ["def func():\n", "  print('buggy')\n"] # Content after failed edit?
        abs_target_path = self._add_file_to_db(target_rel, original_content)
        
        # Simulate previous failed edit attempt details
        self.db_for_test["last_edit_params"] = {
            "target_file": abs_target_path,
            "code_edit": "# ...\n  print('fixed') # ...", # The proposal that maybe failed
            "instructions": "I will fix the print statement in func.",
            "explanation": "Attempt 1"
        }
        
        # Mock LLM response (the expected final correct content)
        expected_final_content_str = "def func():\n  print('correctly fixed')\n"
        self.mock_call_llm.return_value = expected_final_content_str

        # Execute the function under test
        result = reapply(target_file=target_rel)

        # Assertions
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("file_path"), abs_target_path)
        self.assertIn("successfully reapplied", result.get("message", ""))

        # Verify LLM was called with correct context
        self.mock_call_llm.assert_called_once()
        prompt_text = self.mock_call_llm.call_args[1]['prompt_text']
        self.assertIn("Original User Instructions:\n\"I will fix the print statement in func.\"", prompt_text)
        self.assertIn("Previously Proposed Code Edit String", prompt_text)
        self.assertIn("".join(original_content), prompt_text) # Current content included

        # Verify DB state updated correctly
        final_content_lines = self._get_file_content_lines(target_rel)
        self.assertEqual(final_content_lines, ["def func():\n", "  print('correctly fixed')\n"])

        # Verify last_edit_params updated
        last_edit = self.db_for_test.get("last_edit_params")
        self.assertEqual(last_edit.get("target_file"), abs_target_path)
        self.assertEqual(last_edit.get("code_edit"), expected_final_content_str) # Stores new content
        self.assertEqual(last_edit.get("instructions"), "I will fix the print statement in func.") # Original instruction kept
        self.assertIn("Reapplied edit", last_edit.get("explanation", ""))


    def test_reapply_fails_if_no_last_edit_params(self):
        """Verify reapply fails if no last edit is recorded."""
        target_rel = "file.txt"
        self._add_file_to_db(target_rel, ["content"])
        self.db_for_test["last_edit_params"] = None # Ensure no last edit

        with self.assertRaises(LastEditNotFoundError) as cm:
            reapply(target_file=target_rel)
        self.assertIn("No relevant previous edit found", str(cm.exception))
        self.mock_call_llm.assert_not_called()

    def test_reapply_fails_if_last_edit_mismatch(self):
        """Verify reapply fails if last edit was for a different file."""
        target_rel = "actual_target.txt"
        other_file_rel = "other_file.txt"
        abs_target_path = self._add_file_to_db(target_rel, ["content"])
        abs_other_path = self._add_file_to_db(other_file_rel, ["other content"])
        self.db_for_test["last_edit_params"] = {
            "target_file": abs_other_path, # Last edit was for other file
            "code_edit": "...", "instructions": "..."
        }

        with self.assertRaises(LastEditNotFoundError) as cm:
            reapply(target_file=target_rel)
        self.assertIn("No relevant previous edit found", str(cm.exception))
        self.mock_call_llm.assert_not_called()

    def test_reapply_fails_if_target_is_directory(self):
        """Verify reapply fails if the target path is a directory."""
        target_rel = "src_dir"
        abs_target_path = self._add_dir_to_db(target_rel)
        # Setup a last edit pointing to this path, although file check should fail first
        self.db_for_test["last_edit_params"] = {
            "target_file": abs_target_path, "code_edit": "...", "instructions": "..."
        }

        with self.assertRaises(IsADirectoryError) as cm:
            reapply(target_file=target_rel)
        self.assertIn("is a directory", str(cm.exception))
        self.mock_call_llm.assert_not_called()

    def test_reapply_handles_llm_failure(self):
        """Verify reapply handles errors during the LLM call."""
        target_rel = "fix_me.py"
        abs_target_path = self._add_file_to_db(target_rel, ["old content"])
        self.db_for_test["last_edit_params"] = {
            "target_file": abs_target_path, "code_edit": "...", "instructions": "Fix it"
        }
        # Simulate LLM raising an error
        self.mock_call_llm.side_effect = LLMGenerationError("Simulated LLM API error")

        with self.assertRaises(LLMGenerationError) as cm:
            reapply(target_file=target_rel)
        
        self.assertIn("Simulated LLM API error", str(cm.exception))
        # Ensure DB state wasn't incorrectly modified
        self.assertEqual(self._get_file_content_lines(target_rel), ["old content\n"])


@unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not set, skipping LLM integration tests for reapply.")
class TestReapplyIntegration(unittest.TestCase):
    """
    Integration tests for the reapply function, making actual LLM calls.
    Requires GEMINI_API_KEY.
    """
    def setUp(self):
        """Prepares an isolated database state."""
        # Create temporary workspace and DB state
        self.workspace_path, self.db_for_test = minimal_reset_db_for_reapply()
        
        self.db_patcher_for_init = patch("cursor.DB", self.db_for_test)
        self.db_patcher_for_init.start()
        self.db_patcher_for_utils = patch("cursor.SimulationEngine.utils.DB", self.db_for_test)
        self.db_patcher_for_utils.start()
        # Patch 'DB' in the cursorAPI module where the actual function is defined
        self.db_patcher_for_cursorapi = patch("cursor.cursorAPI.DB", self.db_for_test)
        self.db_patcher_for_cursorapi.start()

    def tearDown(self):
        """Restores original state."""
        self.db_patcher_for_cursorapi.stop()
        self.db_patcher_for_utils.stop()
        self.db_patcher_for_init.stop()
        
        # Clean up temporary workspace
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    # Simplified helpers duplicated for this class
    def _add_dir_to_db(self, path: str, is_abs: bool = False):
        abs_path = path if is_abs else os.path.normpath(os.path.join(self.workspace_path, path))
        if abs_path not in self.db_for_test["file_system"]:
            # Create the directory on filesystem
            os.makedirs(abs_path, exist_ok=True)
            
            self.db_for_test["file_system"][abs_path] = {
                "path": abs_path, 
                "is_directory": True, 
                "content_lines": [], 
                "size_bytes": 0, 
                "last_modified": utils.get_current_timestamp_iso()
            }
        parent_dir = os.path.dirname(abs_path)
        if parent_dir and parent_dir != abs_path and parent_dir != self.workspace_path and parent_dir not in self.db_for_test["file_system"] and parent_dir != os.path.dirname(self.workspace_path):
            self._add_dir_to_db(parent_dir, is_abs=True)

    def _add_file_to_db(self, path: str, content_lines_raw: list[str]):
        abs_path = os.path.normpath(os.path.join(self.workspace_path, path)) # Assume relative
        dir_name = os.path.dirname(abs_path)
        if dir_name and dir_name != self.workspace_path and dir_name not in self.db_for_test["file_system"]:
            self._add_dir_to_db(dir_name, is_abs=True)
        content_lines = utils._normalize_lines(content_lines_raw, ensure_trailing_newline=True)
        
        # Create the file on filesystem
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(content_lines)
        
        self.db_for_test["file_system"][abs_path] = {
            "path": abs_path, 
            "is_directory": False, 
            "content_lines": content_lines,
            "size_bytes": utils.calculate_size_bytes(content_lines), 
            "last_modified": utils.get_current_timestamp_iso()
        }
        return abs_path

    def _get_file_content_lines(self, path_rel_to_ws_root: str):
        abs_path = os.path.normpath(os.path.join(self.workspace_path, path_rel_to_ws_root))
        entry = self.db_for_test.get("file_system", {}).get(abs_path)
        return entry.get("content_lines", []) if entry and not entry.get("is_directory") else None

    # --- Live LLM Reapply Tests ---

    def test_live_reapply_fix_simple_error(self):
        """Integration test: Reapply to fix a simple incorrect modification."""
        target_file_rel = "simple_fix.py"
        # Simulate state after a bad edit tried to add logging INCORRECTLY
        initial_content = [
            "def calculate(a, b):\n",
            "    result = a + b # Incorrect log added here\n", # Original was just a+b
            "    return result\n"
        ]
        abs_target_path = self._add_file_to_db(target_file_rel, initial_content)

        # Last edit params that led to the bad state
        self.db_for_test["last_edit_params"] = {
            "target_file": abs_target_path,
            "code_edit": "// ... existing code ...\n    result = a + b # Incorrect log added here\n// ... existing code ...",
            "instructions": "I will add logging before the return statement in calculate.",
            "explanation": "Initial attempt"
        }
        
        print(f"\n[LIVE REAPPLY TEST - FIX] Requesting reapply for: {target_file_rel}")
        # Execute reapply - LLM should see original instruction and current flawed state
        result = reapply(target_file=target_file_rel)
        print(f"  Reapply Result: Message: {result.get('message')}")

        self.assertIsInstance(result, dict)
        self.assertIn("successfully reapplied", result.get("message", ""))
        self.assertEqual(result.get("file_path"), abs_target_path)
        
        final_content = self._get_file_content_lines(target_file_rel)
        final_content_str = "".join(final_content) if final_content else ""
        print(f"  Final Content after Reapply:\n{final_content_str}")

        # Flexible assertions: Check if logging is added (likely before return)
        # and the core calculation is still present.
        self.assertIn("def calculate(a, b):", final_content_str)
        self.assertTrue("log" in final_content_str.lower() or "print" in final_content_str.lower(), "Expected some form of logging/printing to be added.")
        
        # More flexible assertion that accepts either direct return or variable-based return
        self.assertTrue(
            "return a + b" in final_content_str or  # Direct calculation return
            ("result = a + b" in final_content_str and "return result" in final_content_str),  # Variable-based return
            "Expected calculation logic to be preserved in some form"
        )


    def test_live_reapply_from_failed_patch(self):
        """Integration test: Reapply after apply_code_edit might have failed previously."""
        target_file_rel = "failed_patch_target.txt"
        # Simulate state where the file exists but maybe unchanged from original after edit_file failed
        original_content = ["Context Line A\n", "Line To Modify\n", "Context Line B\n"]
        abs_target_path = self._add_file_to_db(target_file_rel, original_content)

        # Last edit params that might have failed due to bad context in original code_edit
        self.db_for_test["last_edit_params"] = {
            "target_file": abs_target_path,
            "code_edit": "Context Line A\n// ... existing code ...\nMODIFIED LINE\n// ... existing code ...\nContext Line ZZZ\n", # Bad trailing context ZZZ
            "instructions": "I will modify the middle line.",
            "explanation": "Initial attempt with bad context"
        }
        
        print(f"\n[LIVE REAPPLY TEST - FAILED PATCH] Requesting reapply for: {target_file_rel}")
        result = reapply(target_file=target_file_rel)
        print(f"  Reapply Result: Message: {result.get('message')}")

        self.assertIsInstance(result, dict)
        self.assertIn("successfully reapplied", result.get("message", ""))
        self.assertEqual(result.get("file_path"), abs_target_path)
        
        final_content = self._get_file_content_lines(target_file_rel)
        final_content_str = "".join(final_content) if final_content else ""
        print(f"  Final Content after Reapply:\n{final_content_str}")

        # Flexible assertions: Check if the middle line was changed and context preserved
        self.assertIn("Context Line A", final_content_str)
        self.assertIn("MODIFIED LINE", final_content_str) # Check if the intended content is there
        self.assertIn("Context Line B", final_content_str)
        self.assertNotIn("Line To Modify", final_content_str) # Ensure old line is gone

    def test_live_reapply_complex_service_refactor(self):
        """Integration test: Reapply on a complex Python service to refactor it significantly."""
        target_file_rel = "complex_service.py"
        
        # Set up a complex Python service file with several methods and classes
        abs_target_path = self._add_file_to_db(target_file_rel, COMPLEX_PYTHON_SERVICE.splitlines())
        
        # Create a code edit string with partial changes that were "unsuccessfully applied" previously
        # This simulates a failed edit attempt that only made some of the needed changes
        partial_code_edit = '''
# service.py
import logging
import os
import json
import time  # New import
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataProcessor:
    """Service class for processing data from various sources."""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path or "config.json")
        self.last_run = None
        self.cache = {}
        self.performance_metrics = {  # Added metrics tracking
            "total_processed": 0,
            "total_errors": 0,
            "processing_time": 0
        }
        
    # ... existing code ...
'''

        # Set up the "failed" previous edit attempt
        self.db_for_test["last_edit_params"] = {
            "target_file": abs_target_path,
            "code_edit": partial_code_edit,
            "instructions": "I will refactor the DataProcessor class to add comprehensive performance tracking, caching improvements, and enhanced data processing capabilities.",
            "explanation": "Previous attempt only started adding performance metrics but didn't complete all necessary changes."
        }
        
        print(f"\n[LIVE COMPLEX REAPPLY TEST] Requesting reapply for: {target_file_rel}")
        
        # Execute reapply - Real LLM should complete the refactoring based on original instructions
        result = reapply(target_file=target_file_rel)
        print(f"  Reapply Result: Message: {result.get('message')}")

        self.assertIsInstance(result, dict)
        self.assertIn("successfully reapplied", result.get("message", ""))
        self.assertEqual(result.get("file_path"), abs_target_path)
        
        # Get the final content after LLM reapply
        final_content = self._get_file_content_lines(target_file_rel)
        final_content_str = "".join(final_content) if final_content else ""
        print(f"  First 200 chars of content after Reapply:\n{final_content_str[:200]}...")
        print(f"  Length of reapplied content: {len(final_content_str)} chars")

        # Assertions for core expected changes - these should be added by any reasonable LLM 
        # implementation of the refactoring instructions
        self.assertIn("import time", final_content_str, "Should add time import for performance tracking")
        self.assertIn("performance_metrics", final_content_str, "Should include performance metrics")
        
        # Check for evidence of comprehensive refactoring (logical requirements fulfilled)
        # Make the timing assertion more flexible to accommodate different LLM implementations
        has_timing_operations = any(term in final_content_str for term in 
                                  ["start_time", "elapsed", "duration", "timer", "performance"])
        self.assertTrue(
            has_timing_operations,
            "Should implement some form of timing or performance tracking"
        )
        
        # Check if processing functionality was enhanced
        has_added_validation = any(term in final_content_str for term in 
                                  ["validate", "validation", "is_valid"])
        has_enhanced_error_handling = "try" in final_content_str and "except" in final_content_str
        
        self.assertTrue(
            has_added_validation or has_enhanced_error_handling,
            "Should enhance data processing with validation or better error handling"
        )
        
        # Verify the LLM completed all original method implementations (not just partial)
        all_expected_methods = [
            "process_item", 
            "process_batch", 
            "clear_cache", 
            "get_stats", 
            "_transform_data"
        ]
        
        for method in all_expected_methods:
            self.assertIn(f"def {method}", final_content_str, 
                         f"Should preserve and enhance the {method} method")

        # Verify the reapply was comprehensive by checking the content length
        # If the LLM properly implemented all functionality, the file should be
        # similar or larger than the original
        original_length = len(COMPLEX_PYTHON_SERVICE)
        self.assertGreaterEqual(
            len(final_content_str), original_length * 0.9,
            "Reapplied content should be at least 90% of the original size"
        )
        
        print(f"  Reapply successful: Completed full refactoring with performance tracking")
        
        # Verify cached edit parameters were updated with the full new content
        last_edit = self.db_for_test.get("last_edit_params")
        self.assertEqual(last_edit.get("target_file"), abs_target_path)
        self.assertNotEqual(last_edit.get("code_edit"), partial_code_edit,
                          "Code edit should be updated with full refactored content")

    def test_live_reapply_react_component_modernization(self):
        """Integration test: Reapply on a React component to modernize it with many changes."""
        target_file_rel = "TaskManager.jsx"
        
        # Set up a complex React component file
        abs_target_path = self._add_file_to_db(target_file_rel, COMPLEX_REACT_COMPONENT.splitlines())
        
        # Create a partial code edit string that was "unsuccessfully applied" previously
        # This simulates a failed edit attempt that only made some of the needed changes
        partial_modernization_edit = '''
// TaskManager.jsx
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
// Using MUI v5 imports instead of v4
import { 
  Container, 
  Grid, 
  Paper, 
  Typography, 
  Button, 
  List, 
  ListItem, 
  ListItemText,
  IconButton,
  TextField,
  CircularProgress
} from '@mui/material';
import { Delete as DeleteIcon, Edit as EditIcon, CheckCircle as CheckIcon } from '@mui/icons-material';

// Using environment variable for API URL
const API_URL = process.env.REACT_APP_API_URL || 'https://api.example.com/tasks';

// Added custom hook for API calls
const useApi = (endpoint) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ... rest of hook implementation missing ...
};

const TaskManager = () => {
  // ... existing code ...
'''

        # Set up the "failed" previous edit attempt
        self.db_for_test["last_edit_params"] = {
            "target_file": abs_target_path,
            "code_edit": partial_modernization_edit,
            "instructions": "I will modernize this React component by: 1) updating Material-UI imports to v5, 2) adding proper TypeScript types, 3) using React hooks for API calls, 4) adding error handling, 5) implementing optimistic updates, and 6) adding task filtering functionality.",
            "explanation": "Previous attempt only started modernizing the imports and creating a custom hook, but didn't complete the implementation."
        }
        
        print(f"\n[LIVE REACT REAPPLY TEST] Requesting reapply for: {target_file_rel}")
        
        # Execute reapply - Real LLM should complete the modernization based on original instructions
        result = reapply(target_file=target_file_rel)
        print(f"  Reapply Result: Message: {result.get('message')}")

        self.assertIsInstance(result, dict)
        self.assertIn("successfully reapplied", result.get("message", ""))
        self.assertEqual(result.get("file_path"), abs_target_path)
        
        # Get the final content after LLM reapply
        final_content = self._get_file_content_lines(target_file_rel)
        final_content_str = "".join(final_content) if final_content else ""
        print(f"  First 200 chars of content after Reapply:\n{final_content_str[:200]}...")
        print(f"  Length of reapplied content: {len(final_content_str)} chars")

        # Assertions for core expected changes - these should be added by any reasonable LLM implementation
        
        # 1. Check for Material-UI v5 imports
        self.assertIn("@mui/material", final_content_str, "Should update to MUI v5 imports")
        self.assertIn("@mui/icons-material", final_content_str, "Should update icon imports")
        
        # 2. Check for TypeScript types
        ts_evidence = any(pattern in final_content_str for pattern in [
            ": React.FC", 
            "interface ", 
            "type ", 
            ": string", 
            ": boolean",
            ": Array<"
        ])
        self.assertTrue(ts_evidence, "Should add TypeScript type annotations")
        
        # 3. Check for custom hooks implementation - make more flexible
        has_hooks_implementation = any(pattern in final_content_str for pattern in [
            "useApi", 
            "useTasks", 
            "useCallback", 
            "useMemo", 
            "useEffect(", 
            "const use",
            "custom hook"
        ])
        self.assertTrue(
            has_hooks_implementation,
            "Should implement or enhance usage of React hooks"
        )
        
        # 4. Check for error handling improvements
        has_try_catch = "try {" in final_content_str and "catch" in final_content_str
        self.assertTrue(has_try_catch, "Should include proper error handling")
        
        # 5. Check for optimistic updates
        has_optimistic_updates = any(pattern in final_content_str for pattern in [
            "optimistic", 
            "prevTasks", 
            "setTasks([...tasks"
        ])
        self.assertTrue(has_optimistic_updates, "Should implement optimistic updates")
        
        # 6. Check for filtering functionality
        has_filtering = any(pattern in final_content_str for pattern in [
            "filter", 
            "filtered", 
            "setFilter"
        ])
        self.assertTrue(has_filtering, "Should add task filtering functionality")
        
        # Ensure all core functionality is preserved
        core_functions = [
            "handleCreateTask", 
            "handleDeleteTask", 
            "handleToggleComplete"
        ]
        for func in core_functions:
            self.assertIn(func, final_content_str, f"Should preserve {func} function")
        
        # Verify the reapply was comprehensive by checking the content length
        original_length = len(COMPLEX_REACT_COMPONENT)
        self.assertGreaterEqual(
            len(final_content_str), original_length * 0.9,
            "Reapplied content should be at least 90% of the original size"
        )
        
        print(f"  Reapply successful: Completed React component modernization")
        
        # Verify cached edit parameters were updated with the full new content
        last_edit = self.db_for_test.get("last_edit_params")
        self.assertEqual(last_edit.get("target_file"), abs_target_path)
        self.assertNotEqual(last_edit.get("code_edit"), partial_modernization_edit,
                          "Code edit should be updated with full modernized content")

class TestReapplyInputValidation(unittest.TestCase):

    def setUp(self):
        """Set up a mock DB for testing."""
        self.workspace_path, self.mock_db = minimal_reset_db_for_reapply()
        # Create a dummy file in the mock file system
        self.test_file_path = os.path.join(self.workspace_path, "test_file.py")
        
        # Create the file on filesystem
        os.makedirs(os.path.dirname(self.test_file_path), exist_ok=True)
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            f.write("print('hello')")
        
        self.mock_db["file_system"][self.test_file_path] = {
            "content_lines": ["print('hello')"],
            "is_directory": False,
        }

    def tearDown(self):
        """Clean up temporary workspace."""
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    @patch('cursor.cursorAPI.DB', new_callable=MagicMock)
    def test_reapply_invalid_target_file_type(self, mock_db):
        """Test that reapply raises TypeError for non-string target_file."""
        mock_db.__getitem__.side_effect = self.mock_db.__getitem__
        mock_db.get.side_effect = self.mock_db.get

        with self.assertRaisesRegex(TypeError, "Argument 'target_file' must be a string"):
            reapply(target_file=123)

    @patch('cursor.cursorAPI.DB', new_callable=MagicMock)
    def test_reapply_empty_target_file(self, mock_db):
        """Test that reapply raises ValueError for an empty string target_file."""
        mock_db.__getitem__.side_effect = self.mock_db.__getitem__
        mock_db.get.side_effect = self.mock_db.get

        with self.assertRaisesRegex(ValueError, "cannot be empty or contain only whitespace"):
            reapply(target_file="")

    @patch('cursor.cursorAPI.DB', new_callable=MagicMock)
    def test_reapply_whitespace_target_file(self, mock_db):
        """Test that reapply raises ValueError for a whitespace-only target_file."""
        mock_db.__getitem__.side_effect = self.mock_db.__getitem__
        mock_db.get.side_effect = self.mock_db.get

        with self.assertRaisesRegex(ValueError, "cannot be empty or contain only whitespace"):
            reapply(target_file="   ")


if __name__ == '__main__':
    unittest.main()