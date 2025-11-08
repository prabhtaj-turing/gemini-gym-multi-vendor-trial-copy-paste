"""
Test cases for vscode_environment module in the Copilot API.
Tests get_vscode_api and install_extension functions.
"""

import unittest
import copy
from typing import Dict, Any

from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from .. import get_vscode_api, install_extension
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestVSCodeEnvironment(BaseTestCaseWithErrorHandler):
    """Test cases for VS Code environment functions."""

    def setUp(self):
        """Set up test fixtures."""
        self._original_DB_state = copy.deepcopy(DB)
        
        # Set up test data for vscode API references
        DB["vscode_api_references"] = [
            {
                "name": "window.showInformationMessage",
                "documentation_summary": "Shows an information message to the user",
                "module": "vscode.window",
                "kind": "function",
                "signature": "showInformationMessage(message: string, ...items: string[]): Thenable<string | undefined>",
                "example_usage": "vscode.window.showInformationMessage('Hello World!');"
            },
            {
                "name": "commands.registerCommand",
                "documentation_summary": "Registers a command that can be invoked via a keyboard shortcut, menu item, or programmatically",
                "module": "vscode.commands",
                "kind": "function",
                "signature": "registerCommand(command: string, callback: (...args: any[]) => any): Disposable",
                "example_usage": "vscode.commands.registerCommand('extension.helloWorld', () => { vscode.window.showInformationMessage('Hello World!'); });"
            },
            {
                "name": "TextDocument",
                "documentation_summary": "Represents a text document, such as a source file",
                "module": "vscode",
                "kind": "interface",
                "signature": None,
                "example_usage": None
            },
            {
                "name": "workspace.openTextDocument",
                "documentation_summary": "Opens a text document",
                "module": "vscode.workspace",
                "kind": "function",
                "signature": "openTextDocument(uri?: Uri): Thenable<TextDocument>",
                "example_usage": "vscode.workspace.openTextDocument(uri).then(doc => { console.log(doc.getText()); });"
            }
        ]
        
        # Set up test data for extension marketplace and installation
        DB["vscode_extensions_marketplace"] = [
            {"id": "ms-python.python", "name": "Python", "publisher": "ms-python"},
            {"id": "ms-vscode.typescript", "name": "TypeScript", "publisher": "ms-vscode"},
            {"id": "ext.test", "name": "Test Extension", "publisher": "ext"}
        ]
        
        DB["installed_vscode_extensions"] = ["ms-vscode.typescript"]
        
        DB["extensions_simulated_install_behavior"] = {
            "ms-python.python": "success",
            "ext.test": "success"
        }
        
        DB["vscode_context"] = {
            "is_new_workspace_creation": True
        }

    def tearDown(self):
        """Clean up after each test."""
        DB.clear()
        DB.update(self._original_DB_state)

    # Note: This file previously contained duplicate tests for get_vscode_api and install_extension
    # Those tests have been moved to dedicated test files: test_get_vscode_api.py and test_install_extention.py
    # This ensures no duplicate test coverage while maintaining organized test structure.
    pass


if __name__ == '__main__':
    unittest.main()
