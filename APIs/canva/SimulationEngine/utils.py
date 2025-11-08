"""
Utility functions for Canva API simulation.

This module provides common utility functions used across the Canva API simulation,
including ID generation and default data creation.
"""

import random
import string
from typing import Dict, Union


def generate_canva_design_id() -> str:
    """
    Generate a Canva-style design ID (11 characters, alphanumeric).
    
    Returns:
        str: A unique design ID in Canva format (e.g., "DAFVztcvd9z").
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=11))


def generate_default_thumbnail() -> Dict[str, Union[str, int]]:
    """
    Generate default thumbnail metadata for new designs.
    
    Returns:
        Dict[str, Union[str, int]]: Thumbnail object with width, height, and url.
    """
    return {
        "width": 595,
        "height": 335,
        "url": "https://document-export.canva.com/default/thumbnail/0001.png?new-design"
    }
