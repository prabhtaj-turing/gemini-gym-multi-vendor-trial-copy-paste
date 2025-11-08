# canva/Canva/Design/__init__.py
"""
This module provides design management functionality for Canva.

It includes functions for creating designs, listing user designs, retrieving design metadata,
and managing design pages with validation and error handling.
"""

# Import functions from organized modules
from .DesignCreation import create_design
from .DesignListing import list_designs
from .DesignRetrieval import get_design, get_design_pages

# Re-export all functions for external access
__all__ = [
    'create_design',
    'list_designs', 
    'get_design',
    'get_design_pages'
]
