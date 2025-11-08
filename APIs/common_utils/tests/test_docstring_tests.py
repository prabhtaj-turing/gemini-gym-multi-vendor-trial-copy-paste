#!/usr/bin/env python3
"""
Tests for docstring_tests module.
"""

import unittest
import ast
from unittest.mock import patch
import common_utils.docstring_tests

class TestDocstringStructureUnit(unittest.TestCase):
    def _validate(self, func_src, func_name):
        tree = ast.parse(func_src)
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == func_name)
        return common_utils.docstring_tests.TestDocstringStructure._validate_function_docstring(node, func_name)

    def test_valid_docstring(self):
        src = '''
def foo(x: int, y: str) -> bool:
    """Summary.
    
    Args:
        x (int): The x value.
        y (str): The y value.
    
    Returns:
        bool: True if valid.
    """
    return True
'''
        valid, errors = self._validate(src, 'foo')
        self.assertTrue(valid)
        self.assertEqual(errors, [])

    def test_missing_docstring(self):
        src = '''
def foo(x, y):
    pass
'''
        valid, errors = self._validate(src, 'foo')
        self.assertFalse(valid)
        self.assertIn("missing a docstring", errors[0])

    def test_empty_docstring(self):
        src = '''
def foo(x, y):
    """"""
    pass
'''
        valid, errors = self._validate(src, 'foo')
        self.assertFalse(valid)
        self.assertIn("missing a docstring", errors[0])

    def test_missing_arg_in_docstring(self):
        src = '''
def foo(x, y):
    """Summary.
    
    Args:
        x (int): The x value.
    """
    pass
'''
        valid, errors = self._validate(src, 'foo')
        self.assertFalse(valid)
        self.assertTrue(any("in the function signature but not documented" in e for e in errors))

    def test_extra_arg_in_docstring(self):
        src = '''
def foo(x):
    """Summary.
    
    Args:
        x (int): The x value.
        y (str): Extra.
    """
    pass
'''
        valid, errors = self._validate(src, 'foo')
        self.assertFalse(valid)
        self.assertTrue(any("documented but not found in the function signature" in e for e in errors))

    def test_type_mismatch(self):
        src = '''
def foo(x: int):
    """Summary.
    
    Args:
        x (str): The x value.
    """
    pass
'''
        valid, errors = self._validate(src, 'foo')
        self.assertFalse(valid)
        self.assertTrue(any("Type mismatch" in e for e in errors))

    def test_return_type_mismatch(self):
        src = '''
def foo(x: int) -> int:
    """Summary.
    
    Args:
        x (int): The x value.
    Returns:
        str: Wrong type.
    """
    return 1
'''
        valid, errors = self._validate(src, 'foo')
        self.assertFalse(valid)
        self.assertTrue(any("Return type mismatch" in e for e in errors))

    def test_missing_return_section(self):
        src = '''
def foo(x: int) -> int:
    """Summary.
    
    Args:
        x (int): The x value.
    """
    return 1
'''
        valid, errors = self._validate(src, 'foo')
        self.assertFalse(valid)
        self.assertTrue(any("missing a 'Returns' section" in e for e in errors))

    def test_class_with_docstring(self):
        src = '''
class Bar:
    """A test class."""
    def foo(self, x: int) -> int:
        """Summary.
        
        Args:
            x (int): The x value.
        Returns:
            int: The result.
        """
        return x
'''
        tree = ast.parse(src)
        class_node = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == 'Bar')
        method_node = next(n for n in class_node.body if isinstance(n, ast.FunctionDef) and n.name == 'foo')
        valid, errors = common_utils.docstring_tests.TestDocstringStructure._validate_function_docstring(method_node, 'foo')
        self.assertTrue(valid)
        self.assertEqual(errors, [])

# Mock/skip all integration-style tests that require filesystem or merging CSVs
import pytest
@pytest.mark.skip(reason="Integration test skipped in unit test mode.")
class TestDocstringStructure(unittest.TestCase):
    pass
@pytest.mark.skip(reason="Integration test skipped in unit test mode.")
class TestDocstringTests(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main() 