# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for GeoSetter Lite
Creates a standalone macOS application bundle
"""

import os
from pathlib import Path

block_cipher = None

# Get the project root directory
project_root = os.path.abspath('.')

# Read version from package __init__.py
def get_version():
    init_file = Path(project_root) / 'geosetter_lite' / '__init__.py'
    with open(init_file, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return '0.0.0'

VERSION = get_version()

# Collect all geosetter_lite package files
a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        # Include data directory with CSV files
        ('data/world_locations.csv', 'data'),
        ('data/README.md', 'data'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebChannel',
        'PIL._imaging',
        # UI components
        'geosetter_lite.ui',
        'geosetter_lite.ui.main_window',
        'geosetter_lite.ui.map_panel',
        'geosetter_lite.ui.map_widget',
        'geosetter_lite.ui.metadata_editor',
        'geosetter_lite.ui.batch_edit_dialog',
        'geosetter_lite.ui.geocoding_dialog',
        'geosetter_lite.ui.geolocation_dialog',
        'geosetter_lite.ui.similarity_dialog',
        'geosetter_lite.ui.settings_dialog',
        'geosetter_lite.ui.progress_dialog',
        'geosetter_lite.ui.rename_dialog',
        'geosetter_lite.ui.table_delegates',
        # Services
        'geosetter_lite.services',
        'geosetter_lite.services.exiftool_service',
        'geosetter_lite.services.location_database',
        'geosetter_lite.services.reverse_geocoding_service',
        'geosetter_lite.services.file_scanner',
        'geosetter_lite.services.ai_service',
        # Models
        'geosetter_lite.models',
        'geosetter_lite.models.image_model',
        # Core
        'geosetter_lite.core',
        'geosetter_lite.core.config',
        'geosetter_lite.core.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GeoSetter Lite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GeoSetter Lite',
)

app = BUNDLE(
    coll,
    name='GeoSetter Lite.app',
    icon='icon/geosetter_lite.icns',
    bundle_identifier='com.asaintsever.geosetter-lite',
    version=VERSION,
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'CFBundleDisplayName': 'GeoSetter Lite',
        'CFBundleGetInfoString': 'Image geotagging and metadata editor',
        'CFBundleName': 'GeoSetter Lite',
        'CFBundleShortVersionString': VERSION,
        'CFBundleVersion': VERSION,
    },
)
