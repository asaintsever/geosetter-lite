"""
GeoSetter Lite - Image Metadata Viewer and Editor
"""

__version__ = "0.4.0"

# Register HEIF/HEIC support for PIL/Pillow
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass  # pillow-heif not installed, HEIF/HEIC support will be unavailable

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
