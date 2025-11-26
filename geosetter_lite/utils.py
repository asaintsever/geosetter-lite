"""
Utility functions for formatting and data conversion
"""
from datetime import datetime
from typing import Optional


def format_date(dt: Optional[datetime]) -> str:
    """
    Format a datetime object to a human-readable string
    
    Args:
        dt: datetime object or None
        
    Returns:
        Formatted date string or empty string if None
    """
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB", "234 KB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_gps_coordinates(latitude: Optional[float], longitude: Optional[float]) -> str:
    """
    Format GPS coordinates to a readable string
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        Formatted GPS string or empty string if coordinates are None
    """
    if latitude is None or longitude is None:
        return ""
    
    lat_dir = "N" if latitude >= 0 else "S"
    lon_dir = "E" if longitude >= 0 else "W"
    
    return f"{abs(latitude):.6f}° {lat_dir}, {abs(longitude):.6f}° {lon_dir}"


def parse_gps_dms(dms_str: str) -> Optional[float]:
    """
    Parse GPS coordinates from DMS (Degrees Minutes Seconds) format to decimal degrees
    
    Args:
        dms_str: DMS string like "40 deg 26' 46.32\" N"
        
    Returns:
        Decimal degrees or None if parsing fails
    """
    if not dms_str:
        return None
    
    try:
        # Remove extra spaces and split
        parts = dms_str.replace("deg", "").replace("'", "").replace('"', "").split()
        
        if len(parts) < 3:
            # Try to parse as decimal
            return float(dms_str)
        
        degrees = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        direction = parts[3] if len(parts) > 3 else ""
        
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        
        # Apply direction
        if direction in ['S', 'W']:
            decimal = -decimal
        
        return decimal
    except (ValueError, IndexError):
        return None


def truncate_string(text: str, max_length: int = 50) -> str:
    """
    Truncate a string to a maximum length with ellipsis
    
    Args:
        text: String to truncate
        max_length: Maximum length
        
    Returns:
        Truncated string
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."

