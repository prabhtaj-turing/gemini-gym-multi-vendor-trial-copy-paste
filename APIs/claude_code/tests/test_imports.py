import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))


class ImportTest(unittest.TestCase):
    def test_import_claude_code_package(self):
        """Test that the main claude_code package can be imported."""
        try:
            import APIs.claude_code
        except ImportError:
            self.fail("Failed to import claude_code package") 

    def test_import_public_functions(self):
        """Test that the public functions are imported."""
        try:
            from APIs.claude_code.file_system import read_file
            from APIs.claude_code.shell import bash
            from APIs.claude_code.todo import todo_write
            from APIs.claude_code.web import web_fetch
            from APIs.claude_code.task import task
            from APIs.claude_code.thinking import think, code_review
        except ImportError:
            self.fail("Failed to import public functions from claude_code package")

    def test_public_functions_are_callable(self):
        """Test that the public functions are callable."""
        from APIs.claude_code.file_system import read_file
        from APIs.claude_code.shell import bash
        from APIs.claude_code.todo import todo_write
        from APIs.claude_code.web import web_fetch
        from APIs.claude_code.task import task
        from APIs.claude_code.thinking import think, code_review
    
        self.assertTrue(callable(read_file))
        self.assertTrue(callable(bash))
        self.assertTrue(callable(todo_write))
        self.assertTrue(callable(web_fetch))
        self.assertTrue(callable(task))
        self.assertTrue(callable(think))
        self.assertTrue(callable(code_review))

    def test_import_simulation_engine_components(self):
        """Test that the simulation engine components are imported."""
        try:
            from APIs.claude_code.SimulationEngine import utils

            from APIs.claude_code.SimulationEngine.custom_errors import (
                CommandExecutionError,
                FileSystemError,
                InvalidCodeError,
                InvalidGlobPatternError,
                InvalidInputError,
                InvalidPathError,
                NotImplementedError,
                ShellSecurityError,
                WorkspaceNotAvailableError,
            )
            from APIs.claude_code.SimulationEngine.db import DB
            from APIs.claude_code.SimulationEngine.models import (
                BashRequest,
                EditFileRequest,
                GrepRequest,
                ListFilesRequest,
                ReadFileRequest,
                SearchGlobRequest,
                TaskRequest,
                TodoItem,
                TodoWriteRequest,
                WebFetchRequest,
            )
        except ImportError as e:
            self.fail(f"Failed to import SimulationEngine components: {e}")

    def test_simulation_engine_components_are_usable(self):
        """Test that imported SimulationEngine components are usable."""
        from APIs.claude_code.SimulationEngine import utils
        from APIs.claude_code.SimulationEngine.custom_errors import (
            CommandExecutionError,
            FileSystemError,
            InvalidCodeError,
            InvalidGlobPatternError,
            InvalidInputError,
            InvalidPathError,
            NotImplementedError,
            ShellSecurityError,
            WorkspaceNotAvailableError,
        )
        from APIs.claude_code.SimulationEngine.db import DB
        from APIs.claude_code.SimulationEngine.models import (
            BashRequest,
            EditFileRequest,
            GrepRequest,
            ListFilesRequest,
            ReadFileRequest,
            SearchGlobRequest,
            TaskRequest,
            TodoItem,
            TodoWriteRequest,
            WebFetchRequest,
        )

        self.assertTrue(hasattr(utils, "resolve_workspace_path"))
        self.assertTrue(hasattr(utils, "with_common_file_system"))
        self.assertTrue(issubclass(CommandExecutionError, Exception))
        self.assertTrue(issubclass(FileSystemError, Exception))
        self.assertTrue(issubclass(InvalidCodeError, Exception))
        self.assertTrue(issubclass(InvalidGlobPatternError, Exception))
        self.assertTrue(issubclass(InvalidInputError, Exception))
        self.assertTrue(issubclass(InvalidPathError, Exception))
        self.assertTrue(issubclass(NotImplementedError, Exception))
        self.assertTrue(issubclass(ShellSecurityError, Exception))
        self.assertTrue(issubclass(WorkspaceNotAvailableError, Exception))
        self.assertIsInstance(DB, dict)
        self.assertTrue(hasattr(BashRequest, "model_validate"))
        self.assertTrue(hasattr(EditFileRequest, "model_validate"))
        self.assertTrue(hasattr(GrepRequest, "model_validate"))
        self.assertTrue(hasattr(ListFilesRequest, "model_validate"))
        self.assertTrue(hasattr(ReadFileRequest, "model_validate"))
        self.assertTrue(hasattr(SearchGlobRequest, "model_validate"))
        self.assertTrue(hasattr(TaskRequest, "model_validate"))
        self.assertTrue(hasattr(TodoItem, "model_validate"))
        self.assertTrue(hasattr(TodoWriteRequest, "model_validate"))
        self.assertTrue(hasattr(WebFetchRequest, "model_validate"))