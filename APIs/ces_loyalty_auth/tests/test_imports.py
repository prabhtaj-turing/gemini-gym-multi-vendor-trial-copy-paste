"""
Test cases for validating the import mechanism of the CES Loyalty Auth API.

This module ensures that all public functions are correctly exposed through the
__init__.py and can be imported directly from the root of the API package.
It uses introspection to dynamically discover the functions that should be public
and verifies that they are accessible.
"""

import unittest
import importlib
import pkgutil
import sys
from .loyalty_auth_base_exception import LoyaltyAuthBaseTestCase


class TestImports(LoyaltyAuthBaseTestCase):
    """
    Test suite for verifying that all public functions in the CES Loyalty Auth API
    are correctly exposed and importable.
    """

    def setUp(self):
        """
        Set up the test environment by identifying the root package of the API.
        This allows the tests to dynamically discover and import modules.
        """
        # Ascertain the root package of the API for dynamic imports
        self.api_root = "ces_loyalty_auth"
        if self.api_root not in sys.modules:
            importlib.import_module(self.api_root)

    def test_all_public_functions_are_importable_from_root(self):
        """
        Verifies that every function defined in the API's __all__ attribute
        can be successfully imported from the root of the package.
        This test ensures that the __init__.py is correctly configured to expose
        all public parts of the API.
        """
        api_module = importlib.import_module(self.api_root)
        public_functions = getattr(api_module, "__all__", [])
        self.assertTrue(
            public_functions,
            f"The __all__ attribute is not defined or is empty in {self.api_root}.__init__.py.",
        )

        for func_name in public_functions:
            with self.subTest(function=func_name):
                try:
                    # Attempt to get the function from the root module
                    getattr(api_module, func_name)
                except AttributeError:
                    self.fail(
                        f"Function '{func_name}' is listed in __all__ but cannot be imported from '{self.api_root}'."
                    )

    def test_no_private_functions_in_all(self):
        """
        Ensures that no private functions (those starting with an underscore)
        are inadvertently included in the __all__ list, which would make them
        part of the public API.
        """
        api_module = importlib.import_module(self.api_root)
        public_functions = getattr(api_module, "__all__", [])
        private_functions = [
            name for name in public_functions if name.startswith("_")
        ]
        self.assertEqual(
            len(private_functions),
            0,
            f"Private functions found in __all__: {', '.join(private_functions)}",
        )

    def test_all_submodules_are_correctly_structured(self):
        """
        Recursively discovers all submodules within the API package and checks
        that they do not raise any syntax errors upon import. This test helps
        catch basic errors in module files across the entire package.
        """
        api_module = sys.modules[self.api_root]
        package_path = api_module.__path__

        for _, name, _ in pkgutil.walk_packages(
            package_path, prefix=f"{self.api_root}."
        ):
            with self.subTest(module=name):
                try:
                    # Attempt to import each discovered submodule
                    importlib.import_module(name)
                except Exception as e:
                    self.fail(f"Failed to import submodule '{name}': {e}")


if __name__ == "__main__":
    unittest.main()
