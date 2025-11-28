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
        'geosetter_lite.main_window',
        'geosetter_lite.map_panel',
        'geosetter_lite.map_widget',
        'geosetter_lite.metadata_editor',
        'geosetter_lite.batch_edit_dialog',
        'geosetter_lite.exiftool_service',
        'geosetter_lite.location_database',
        'geosetter_lite.reverse_geocoding_service',
        'geosetter_lite.file_scanner',
        'geosetter_lite.image_model',
        'geosetter_lite.table_delegates',
        'geosetter_lite.geocoding_dialog',
        'geosetter_lite.geolocation_dialog',
        'geosetter_lite.similarity_dialog',
        'geosetter_lite.settings_dialog',
        'geosetter_lite.progress_dialog',
        'geosetter_lite.ai_service',
        'geosetter_lite.config',
        'geosetter_lite.utils',
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
    icon=None,  # Add icon path if you have one: '_img/icon.icns'
    bundle_identifier='com.asaintsever.geosetter-lite',
    version='0.1.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'CFBundleDisplayName': 'GeoSetter Lite',
        'CFBundleGetInfoString': 'Image geotagging and metadata editor',
        'CFBundleName': 'GeoSetter Lite',
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '0.1.0',
    },
)
