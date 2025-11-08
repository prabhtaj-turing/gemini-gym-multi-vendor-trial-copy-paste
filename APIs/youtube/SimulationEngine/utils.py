# APIs/youtube/SimulationEngine/utils.py
from typing import List
from youtube.SimulationEngine.db import DB
import random
import string


# Utility function to generate random string of a given length
def generate_random_string(length):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


# Utility function to generate unique IDs for various entities
def generate_entity_id(entity_type):
    if entity_type == "caption":
        # ID pattern: CPT + random alphanumeric string of 9 characters
        return f"CPT{generate_random_string(9)}"
    elif entity_type == "channel":
        # ID pattern: UC + random alphanumeric string of 8 characters
        return f"UC{generate_random_string(8)}"
    elif entity_type == "channelSection":
        # ID pattern: section + random alphanumeric string of 6 characters
        return f"CHsec{generate_random_string(6)}"
    elif entity_type == "video":
        # ID pattern: VID + random alphanumeric string of 10 characters
        return f"VID{generate_random_string(10)}"
    elif entity_type == "comment":
        # ID pattern: CMT + random alphanumeric string of 7 characters
        return f"CMT{generate_random_string(7)}"
    elif entity_type == "commentthread":
        # ID pattern: CMT + random alphanumeric string of 5 characters
        return f"CMTTHTR{generate_random_string(5)}"
    elif entity_type == "subscription":
        # ID pattern: SUB + random alphanumeric string of 3 characters
        return f"SUBsub{generate_random_string(3)}"
    elif entity_type == "member":
        # ID pattern: MBR + random alphanumeric string of 6 characters
        return f"MBR{generate_random_string(6)}"
    elif entity_type == "playlist":
        # ID pattern: PL + random alphanumeric string of 10 characters
        return f"PL{generate_random_string(10)}"
    else:
        raise ValueError("Unknown entity type")

def _validate_parameter(value: str, valid_values: List[str], param_name: str) -> None:
    """Validate a parameter against allowed values."""
    if value is not None and value not in valid_values:
        raise ValueError(f"Invalid {param_name} parameter: {value}. Valid values are: {', '.join(valid_values)}")
