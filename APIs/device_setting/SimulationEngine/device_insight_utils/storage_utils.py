"""
Storage utility functions for device insights
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

from device_setting.SimulationEngine.utils import (
    get_setting, get_device_info, set_device_insight_field, get_device_insight_data
)
from device_setting.SimulationEngine.enums import Constants, StorageStatus


def _set_storage_insight_field(field: str, value: Any) -> None:
    """Set a storage insight field in the database.
    
    Args:
        field (str): Field name to set
        value (Any): Value to set
    """
    set_device_insight_field(Constants.STORAGE.value, field, value)


def _get_storage_insights() -> Dict[str, Any]:
    """Get storage insights from the database.
    
    Returns:
        Dict[str, Any]: Storage insights data
    """
    return get_device_insight_data(Constants.STORAGE.value)


def get_storage_insights() -> Dict[str, Any]:
    """
    Get all storage insights from the database.
    
    Returns:
        Dict[str, Any]: All storage insights data
    """
    return _get_storage_insights()


def calculate_storage_percentage() -> float:
    """
    Calculate the percentage of storage used based on current values.
    
    Returns:
        float: Percentage of storage used (0.0 to 100.0), or 0.0 if data is unavailable
    
    Example:
        percentage = calculate_storage_percentage()
        print(f"Storage usage: {percentage:.1f}%")
    """
    total_gb = get_storage_total_gb()
    used_gb = get_storage_used_gb()
    
    if total_gb <= 0:
        return 0.0
    
    return (used_gb / total_gb) * 100.0


def get_storage_status() -> str:
    """
    Get a human-readable storage status based on current usage.
    
    Returns:
        str: Storage status description (e.g., "Low storage", "Normal", "Critical")
    
    Example:
        status = get_storage_status()
        print(f"Storage status: {status}")
    """
    percentage = calculate_storage_percentage()
    
    if percentage >= 90:
        return StorageStatus.CRITICAL.value
    elif percentage >= 80:
        return StorageStatus.LOW.value
    elif percentage >= 60:
        return StorageStatus.MODERATE.value
    else:
        return StorageStatus.NORMAL.value


# Add missing functions that tests expect
def set_storage_total_gb(capacity_gb: int) -> None:
    """
    Set the total storage capacity in GB in device_insights section of the in-memory DB.
    
    Args:
        capacity_gb (int): Total storage capacity in GB
    """
    if not isinstance(capacity_gb, int) or capacity_gb < 0:
        raise ValueError("Total storage must be a non-negative integer")
    
    _set_storage_insight_field(Constants.TOTAL_GB.value, capacity_gb)


def get_storage_total_gb() -> int:
    """
    Get the total storage capacity in GB from device_insights section of the in-memory DB.
    
    Returns:
        int: Total storage capacity in GB or 0 if not set
    """
    try:
        insights = _get_storage_insights()
        return insights.get(Constants.TOTAL_GB.value, 0)
    except Exception:
        return 0


def set_storage_used_gb(used_gb: int) -> None:
    """
    Set the used storage space in GB in device_insights section of the in-memory DB.
    
    Args:
        used_gb (int): Used storage space in GB
    """
    if not isinstance(used_gb, int) or used_gb < 0:
        raise ValueError("Used storage must be a non-negative integer")
    
    _set_storage_insight_field(Constants.USED_GB.value, used_gb)


def get_storage_used_gb() -> int:
    """
    Get the used storage space in GB from device_insights section of the in-memory DB.
    
    Returns:
        int: Used storage space in GB or 0 if not set
    """
    insights = _get_storage_insights()
    return insights.get(Constants.USED_GB.value, 0)


def set_storage_available_gb(available_gb: int) -> None:
    """
    Set the available storage space in GB in device_insights section of the in-memory DB.
    
    Args:
        available_gb (int): Available storage space in GB
    """
    if not isinstance(available_gb, int) or available_gb < 0:
        raise ValueError("Available storage must be a non-negative integer")
    
    _set_storage_insight_field(Constants.AVAILABLE_GB.value, available_gb)


def get_storage_available_gb() -> int:
    """
    Get the available storage space in GB from device_insights section of the in-memory DB.
    
    Returns:
        int: Available storage space in GB or 0 if not set
    """
    insights = _get_storage_insights()
    return insights.get(Constants.AVAILABLE_GB.value, 0)


def set_storage_usage_breakdown(breakdown: Dict[str, float]) -> None:
    """
    Set the storage usage breakdown in device_insights section of the in-memory DB.
    
    Args:
        breakdown (Dict[str, float]): Storage usage breakdown by category (e.g., {"apps": 15.5, "photos": 8.2})
    """
    if not isinstance(breakdown, dict):
        raise ValueError("Usage breakdown must be a dictionary")
    
    for category, space in breakdown.items():
        if not isinstance(space, (int, float)) or space < 0:
            raise ValueError(f"Storage space for category '{category}' must be a non-negative number")
    
    _set_storage_insight_field(Constants.USAGE_BREAKDOWN.value, breakdown)


def get_storage_usage_breakdown() -> Dict[str, float]:
    """
    Get the storage usage breakdown from device_insights section of the in-memory DB.
    
    Returns:
        Dict[str, float]: Storage usage breakdown by category or empty dict if not set
    """
    insights = _get_storage_insights()
    return insights.get(Constants.USAGE_BREAKDOWN.value, {})


def set_storage_insights(
    total_gb: Optional[int] = None,
    used_gb: Optional[int] = None,
    available_gb: Optional[int] = None,
    usage_breakdown: Optional[Dict[str, float]] = None
) -> None:
    """
    Set multiple storage insights at once.
    
    Args:
        total_gb (Optional[int]): Total storage capacity in GB
        used_gb (Optional[int]): Used storage space in GB
        available_gb (Optional[int]): Available storage space in GB
        usage_breakdown (Optional[Dict[str, float]]): Storage usage breakdown by category
    """
    if total_gb is not None:
        set_storage_total_gb(total_gb)
    if used_gb is not None:
        set_storage_used_gb(used_gb)
    if available_gb is not None:
        set_storage_available_gb(available_gb)
    if usage_breakdown is not None:
        set_storage_usage_breakdown(usage_breakdown)
