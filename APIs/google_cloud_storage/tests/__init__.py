"""Test package for google_cloud_storage."""

# Ensure repository root is on sys.path so that stub packages like 'pydantic'
# and top-level modules are importable when pytest adjusts the working
# directory.
import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
