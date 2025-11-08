"""
General utility functions for device insights
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

from device_setting.SimulationEngine.utils import (
    get_setting, get_device_info, set_device_insight_field, get_device_insight_data,
    set_device_id, get_device_id
)
from device_setting.SimulationEngine.enums import Constants, NetworkSignal, DeviceStatus


def set_device_id_insight(device_id: str) -> None:
    """
    Set the device_id in device_insights section of the in-memory DB.
    
    Args:
        device_id (str): Device ID to set
    """
    if not isinstance(device_id, str) or not device_id.strip():
        raise ValueError("Device ID must be a non-empty string")
    
    set_device_id(device_id.strip())


def get_device_id_insight() -> Optional[str]:
    """
    Get the device_id from device_insights section of the in-memory DB.
    
    Returns:
        Optional[str]: Device ID if set, None otherwise
    """
    return get_device_id()


def _set_general_insight_field(field: str, value: Any) -> None:
    """Set a general insight field in the database.
    
    Args:
        field (str): Field name to set
        value (Any): Value to set
    """
    set_device_insight_field(Constants.UNCATEGORIZED.value, field, value)


def _get_general_insights() -> Dict[str, Any]:
    """Get general insights from the database.
    
    Returns:
        Dict[str, Any]: General insights data
    """
    return get_device_insight_data(Constants.UNCATEGORIZED.value)


def set_network_signal_strength(strength: str) -> None:
    """
    Set the network signal strength in device_insights section of the in-memory DB.
    
    Args:
        strength (str): Network signal strength ('excellent', 'good', 'fair', 'poor')
    """
    valid_strengths = [status.value for status in NetworkSignal]
    if strength not in valid_strengths:
        raise ValueError(f"Network signal strength must be one of: {valid_strengths}")
    
    _set_general_insight_field(Constants.NETWORK_SIGNAL.value, strength)


def set_wifi_signal_strength(strength: str) -> None:
    """
    Set the WiFi signal strength in device_insights section of the in-memory DB.
    
    Args:
        strength (str): WiFi signal strength ('excellent', 'good', 'fair', 'poor')
    """
    valid_strengths = [status.value for status in NetworkSignal]
    if strength not in valid_strengths:
        raise ValueError(f"WiFi signal strength must be one of: {valid_strengths}")
    
    _set_general_insight_field(Constants.WIFI_STRENGTH.value, strength)


def set_cellular_signal_strength(strength: str) -> None:
    """
    Set the cellular signal strength in device_insights section of the in-memory DB.
    
    Args:
        strength (str): Cellular signal strength ('excellent', 'good', 'fair', 'poor')
    """
    valid_strengths = [status.value for status in NetworkSignal]
    if strength not in valid_strengths:
        raise ValueError(f"Cellular signal strength must be one of: {valid_strengths}")
    
    _set_general_insight_field(Constants.CELLULAR_SIGNAL.value, strength)


def set_memory_usage_percentage(percentage: int) -> None:
    """
    Set the memory usage percentage in device_insights section of the in-memory DB.
    
    Args:
        percentage (int): Memory usage percentage (0-100)
    """
    if not isinstance(percentage, int) or percentage < 0 or percentage > 100:
        raise ValueError("Memory usage percentage must be an integer between 0 and 100")
    
    _set_general_insight_field(Constants.MEMORY_USAGE.value, percentage)


def set_cpu_usage_percentage(percentage: int) -> None:
    """
    Set the CPU usage percentage in device_insights section of the in-memory DB.
    
    Args:
        percentage (int): CPU usage percentage (0-100)
    """
    if not isinstance(percentage, int) or percentage < 0 or percentage > 100:
        raise ValueError("CPU usage percentage must be an integer between 0 and 100")
    
    _set_general_insight_field(Constants.CPU_USAGE.value, percentage)


def get_general_insights() -> Dict[str, Any]:
    """
    Get all general insights from the database, always including device_id if present.
    
    Returns:
        Dict[str, Any]: All general insights data
    """
    from device_setting.SimulationEngine.db import DB
    from device_setting.SimulationEngine.enums import Constants
    insights = get_device_insight_data(Constants.UNCATEGORIZED.value)
    device_id = DB.get(Constants.DEVICE_INSIGHTS.value, {}).get(Constants.DEVICE_ID.value)
    result = {str(k.value) if hasattr(k, 'value') else str(k): v for k, v in insights.items()}
    if device_id is not None:
        result[Constants.DEVICE_ID.value] = device_id
    return result


# Add missing functions that tests expect
def set_network_signal(signal: str) -> None:
    """
    Set the network signal in device_insights section of the in-memory DB.
    
    Args:
        signal (str): Network signal ('excellent', 'good', 'fair', 'poor')
    """
    set_network_signal_strength(signal)


def get_network_signal() -> str:
    """
    Get the network signal from device_insights section of the in-memory DB.
    
    Returns:
        str: Network signal strength or empty string if not set
    """
    insights = _get_general_insights()
    return insights.get(Constants.NETWORK_SIGNAL.value, "")


def set_wifi_strength(strength: int) -> None:
    """
    Set the WiFi signal strength in device_insights section of the in-memory DB.
    
    Args:
        strength (int): WiFi signal strength (0-100)
    """
    if not isinstance(strength, int) or strength < 0 or strength > 100:
        raise ValueError("WiFi strength must be an integer between 0 and 100")
    
    _set_general_insight_field(Constants.WIFI_STRENGTH.value, strength)


def get_wifi_strength() -> int:
    """
    Get the WiFi signal strength from device_insights section of the in-memory DB.
    
    Returns:
        int: WiFi signal strength or 0 if not set
    """
    insights = _get_general_insights()
    return insights.get(Constants.WIFI_STRENGTH.value, 0)


def set_cellular_signal(signal: int) -> None:
    """
    Set the cellular signal strength in device_insights section of the in-memory DB.
    
    Args:
        signal (int): Cellular signal strength (0-5)
    """
    if not isinstance(signal, int) or signal < 0 or signal > 5:
        raise ValueError("Cellular signal must be an integer between 0 and 5")
    
    _set_general_insight_field(Constants.CELLULAR_SIGNAL.value, signal)


def get_cellular_signal() -> int:
    """
    Get the cellular signal strength from device_insights section of the in-memory DB.
    
    Returns:
        int: Cellular signal strength or 0 if not set
    """
    insights = _get_general_insights()
    return insights.get(Constants.CELLULAR_SIGNAL.value, 0)


def set_memory_usage(percentage: int) -> None:
    """
    Set the memory usage percentage in device_insights section of the in-memory DB.
    
    Args:
        percentage (int): Memory usage percentage (0-100)
    """
    if not isinstance(percentage, int) or percentage < 0 or percentage > 100:
        raise ValueError("Memory usage must be an integer between 0 and 100")
    set_memory_usage_percentage(percentage)


def get_memory_usage() -> int:
    """
    Get the memory usage percentage from device_insights section of the in-memory DB.
    
    Returns:
        int: Memory usage percentage or 0 if not set
    """
    insights = _get_general_insights()
    return insights.get(Constants.MEMORY_USAGE.value, 0)


def set_cpu_usage(percentage: int) -> None:
    """
    Set the CPU usage percentage in device_insights section of the in-memory DB.
    
    Args:
        percentage (int): CPU usage percentage (0-100)
    """
    if not isinstance(percentage, int) or percentage < 0 or percentage > 100:
        raise ValueError("CPU usage must be an integer between 0 and 100")
    set_cpu_usage_percentage(percentage)


def get_cpu_usage() -> int:
    """
    Get the CPU usage percentage from device_insights section of the in-memory DB.
    
    Returns:
        int: CPU usage percentage or 0 if not set
    """
    insights = _get_general_insights()
    return insights.get(Constants.CPU_USAGE.value, 0)


def set_general_insights(
    network_signal: Optional[str] = None,
    wifi_strength: Optional[int] = None,
    cellular_signal: Optional[int] = None,
    memory_usage: Optional[int] = None,
    cpu_usage: Optional[int] = None,
    device_id: Optional[str] = None
) -> None:
    """
    Set multiple general insights at once.
    
    Args:
        network_signal (Optional[str]): Network signal strength
        wifi_strength (Optional[int]): WiFi signal strength (0-100)
        cellular_signal (Optional[int]): Cellular signal strength (0-5)
        memory_usage (Optional[int]): Memory usage percentage (0-100)
        cpu_usage (Optional[int]): CPU usage percentage (0-100)
    """
    if network_signal is not None:
        set_network_signal(network_signal)
    if wifi_strength is not None:
        set_wifi_strength(wifi_strength)
    if cellular_signal is not None:
        set_cellular_signal(cellular_signal)
    if memory_usage is not None:
        set_memory_usage(memory_usage)
    if cpu_usage is not None:
        set_cpu_usage(cpu_usage)
    if device_id is not None:
        set_device_id(device_id)


def get_device_status() -> str:
    """
    Get the overall device status based on current insights.
    
    Returns:
        str: Device status ('Optimal', 'Good', 'Fair', 'Poor')
    """
    insights = _get_general_insights()
    
    # Calculate scores
    wifi_score = insights.get(Constants.WIFI_STRENGTH.value, 0)
    cellular_score = insights.get(Constants.CELLULAR_SIGNAL.value, 0) * 20  # Convert 0-5 to 0-100
    memory_score = 100 - insights.get(Constants.MEMORY_USAGE.value, 0)  # Lower usage is better
    cpu_score = 100 - insights.get(Constants.CPU_USAGE.value, 0)  # Lower usage is better
    
    # Average score
    avg_score = (wifi_score + cellular_score + memory_score + cpu_score) / 4
    
    if avg_score >= 80:
        return DeviceStatus.OPTIMAL.value
    elif avg_score >= 60:
        return DeviceStatus.GOOD.value
    elif avg_score >= 40:
        return DeviceStatus.FAIR.value
    else:
        return DeviceStatus.POOR.value 