"""
GeoSetter Lite - Image Metadata Viewer and Editor
"""

__version__ = "0.3.0"

# Export main components for convenience
from .ui import MainWindow
from .services import ExifToolService, ExifToolError
from .models import ImageModel
from .core import Config

__all__ = [
    'MainWindow',
    'ExifToolService',
    'ExifToolError',
    'ImageModel',
    'Config',
    '__version__',
]
