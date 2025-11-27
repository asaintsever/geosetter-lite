"""
Main Window - Image list and viewer
"""
from pathlib import Path
from typing import List, Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QLabel, QScrollArea, QMenu,
    QHeaderView, QMessageBox, QDialog, QPushButton
)
from PySide6.QtCore import Qt, Signal, QEvent, QSize, QPoint
from PySide6.QtGui import QPixmap, QAction, QImage, QKeyEvent, QIcon, QPainter, QColor, QPen
from PIL import Image
import io
from .image_model import ImageModel
from .file_scanner import FileScanner
from .exiftool_service import ExifToolService
from .metadata_editor import MetadataEditor
from .map_panel import MapPanel
from .table_delegates import CountryDelegate, DateTimeDelegate, TZOffsetDelegate
from .utils import format_date, format_file_size, format_gps_coordinates
from .reverse_geocoding_service import ReverseGeocodingService
from .geocoding_dialog import GeocodingDialog
from .config import Config
from .settings_dialog import SettingsDialog
from .ai_service import AIService
from .similarity_dialog import SimilarityDialog
from .geolocation_dialog import GeolocationDialog
from .progress_dialog import ProgressDialog
from .batch_edit_dialog import BatchEditDialog


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, directory: Path, exiftool_service: ExifToolService):
        """
        Initialize the main window
        
        Args:
            directory: Directory containing images to display
            exiftool_service: ExifTool service instance
        """
        super().__init__()
        self.directory = directory
        self.exiftool_service = exiftool_service
        self.images: List[ImageModel] = []
        self.current_image: Optional[ImageModel] = None
        self.reverse_geocoding_service = ReverseGeocodingService()
        
        # Initialize AI service
        ai_settings = Config.get_ai_settings()
        self.ai_service = AIService(ai_settings['model_cache_dir'])
        
        self.setWindowTitle(f"Image Metadata Viewer - {directory.name}")
        self.setMinimumSize(1200, 700)
        
        # Column metadata mapping for clear operations
        self.column_metadata_map = {
            0: None,  # Filename - cannot be cleared
            1: {'tags': ['EXIF:DateTimeOriginal', 'XMP-exif:DateTimeOriginal'], 'field': 'taken_date'},
            2: {'tags': ['EXIF:TimeZoneOffset', 'EXIF:OffsetTime', 'EXIF:OffsetTimeOriginal', 'EXIF:OffsetTimeDigitized'], 'field': 'tz_offset'},
            3: {'tags': ['EXIF:GPSLatitude', 'EXIF:GPSLongitude', 'EXIF:GPSLatitudeRef', 'EXIF:GPSLongitudeRef'], 'field': 'gps_coordinates'},
            4: {'tags': ['XMP-photoshop:City', 'IPTC:City'], 'field': 'city'},
            5: {'tags': ['XMP-iptcCore:Location', 'IPTC:Sub-location'], 'field': 'sublocation'},
            6: {'tags': ['IPTC:Headline', 'XMP-photoshop:Headline'], 'field': 'headline'},
            7: {'tags': ['EXIF:Model'], 'field': 'camera_model'},
            8: None,  # Size - cannot be cleared
            9: {'tags': ['EXIF:GPSDateStamp', 'EXIF:GPSTimeStamp', 'XMP-exif:GPSDateTime'], 'field': 'gps_date'},
            10: {'tags': ['XMP-photoshop:Country', 'IPTC:Country-PrimaryLocationName', 'XMP-iptcCore:CountryCode', 'IPTC:Country-PrimaryLocationCode'], 'field': 'country'},
            11: {'tags': ['IPTC:Keywords', 'XMP-dc:Subject'], 'field': 'keywords'},
            12: {'tags': ['EXIF:CreateDate', 'XMP-exif:DateTimeDigitized'], 'field': 'created_date'}
        }
        
        self.init_ui()
        self.load_images()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create main horizontal splitter (left side | right side)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # LEFT SIDE: Vertical splitter for image list (top) and image viewer (bottom)
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top-left panel - Image list table
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "Filename",           # 0
            "Taken Date",        # 1
            "TZ Offset",         # 2
            "GPS Coordinates",   # 3
            "City",              # 4
            "Sublocation",       # 5
            "Headline",          # 6
            "Camera Model",      # 7
            "Size",              # 8
            "GPS Date",          # 9
            "Country",           # 10
            "Keywords",          # 11
            "Created Date"       # 12
        ])
        
        # Configure table
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # Make scrollbars always visible
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # Force scrollbars to be visible on macOS (override system auto-hide behavior)
        # Get the scrollbars and make them always visible
        h_scrollbar = self.table.horizontalScrollBar()
        v_scrollbar = self.table.verticalScrollBar()
        if h_scrollbar:
            h_scrollbar.setStyleSheet("QScrollBar:horizontal { height: 15px; }")
        if v_scrollbar:
            v_scrollbar.setStyleSheet("QScrollBar:vertical { width: 15px; }")
        
        # Connect signals
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.itemChanged.connect(self.on_item_changed)
        
        # Install event filter to handle Delete/Backspace keys
        self.table.installEventFilter(self)
        
        # Adjust column widths
        header = self.table.horizontalHeader()
        # All columns use Interactive mode (user can resize)
        for i in range(0, 13):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        
        # Set reasonable default widths for columns
        self.table.setColumnWidth(0, 200)  # Filename
        self.table.setColumnWidth(1, 150)  # Taken Date
        self.table.setColumnWidth(2, 100)  # TZ Offset
        self.table.setColumnWidth(3, 150)  # GPS Coordinates
        self.table.setColumnWidth(4, 120)  # City
        self.table.setColumnWidth(5, 120)  # Sublocation
        self.table.setColumnWidth(6, 150)  # Headline
        self.table.setColumnWidth(7, 120)  # Camera Model
        self.table.setColumnWidth(8, 80)   # Size
        self.table.setColumnWidth(9, 150)  # GPS Date
        self.table.setColumnWidth(10, 150) # Country
        self.table.setColumnWidth(11, 200) # Keywords
        self.table.setColumnWidth(12, 150) # Created Date
        
        # Set custom delegates for country column
        country_col = 10   # Country column index
        self.table.setItemDelegateForColumn(country_col, CountryDelegate(self, self.table))
        
        # Set DateTimeDelegate for date columns
        datetime_delegate = DateTimeDelegate(self, self.table)
        self.table.setItemDelegateForColumn(1, datetime_delegate)   # Taken Date
        self.table.setItemDelegateForColumn(9, datetime_delegate)   # GPS Date
        self.table.setItemDelegateForColumn(12, datetime_delegate)  # Created Date
        
        # Set TZOffsetDelegate for TZ Offset column
        tz_offset_col = 2  # TZ Offset column index
        self.table.setItemDelegateForColumn(tz_offset_col, TZOffsetDelegate(self, self.table))
        
        # Setup header with clear buttons
        self._setup_header_buttons()
        
        left_splitter.addWidget(self.table)
        
        # Bottom-left panel - Image viewer
        self.image_viewer = QLabel()
        self.image_viewer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_viewer.setStyleSheet("background-color: #2b2b2b; color: #888;")
        self.image_viewer.setText("Select an image to view")
        
        # Scroll area for image viewer
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_viewer)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        
        left_splitter.addWidget(scroll_area)
        
        # Set initial left splitter sizes (60% table, 40% viewer)
        left_splitter.setSizes([400, 300])
        
        # Add left side to main splitter
        main_splitter.addWidget(left_splitter)
        
        # RIGHT SIDE: Map panel (with toolbar)
        self.map_panel = MapPanel()
        self.map_panel.setMinimumWidth(300)
        
        # Connect map panel signals
        self.map_panel.update_coordinates_requested.connect(self.update_selected_images_gps)
        self.map_panel.set_marker_from_selection_requested.connect(self.set_marker_from_selected_image)
        self.map_panel.batch_edit_requested.connect(self.batch_edit_metadata)
        self.map_panel.repair_metadata_requested.connect(self.repair_selected_images_metadata)
        self.map_panel.set_taken_date_from_creation_requested.connect(self.set_taken_date_from_creation)
        self.map_panel.set_gps_date_from_taken_requested.connect(self.set_gps_date_from_taken)
        self.map_panel.map_widget.map_clicked.connect(self.on_map_clicked)
        
        main_splitter.addWidget(self.map_panel)
        
        # Set initial main splitter sizes (60% left, 40% right)
        main_splitter.setSizes([700, 500])
        
        main_layout.addWidget(main_splitter)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def _create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        # AI Tools menu
        ai_menu = menubar.addMenu("AI Tools")
        
        # Photo Similarity
        similarity_action = QAction("Find Similar Photos...", self)
        similarity_action.triggered.connect(self._find_similar_photos)
        ai_menu.addAction(similarity_action)
        
        # Geolocation
        geolocation_action = QAction("Predict Locations...", self)
        geolocation_action.triggered.connect(self._predict_locations)
        ai_menu.addAction(geolocation_action)
        
        ai_menu.addSeparator()
        
        # Settings
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self._show_ai_settings)
        ai_menu.addAction(settings_action)
        
        # Application menu (Help menu on most platforms)
        help_menu = menubar.addMenu("Help")
        
        # About action
        about_action = QAction("About GeoSetter Lite", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
    
    def _show_about_dialog(self):
        """Show the About dialog"""
        about_text = """
        <h2>GeoSetter Lite</h2>
        <p><b>Version:</b> 0.1.0</p>
        <p><b>Description:</b> Image Metadata Viewer and Editor</p>
        <br>
        <p>A comprehensive application for viewing and editing EXIF/IPTC/XMP metadata 
        of images with advanced geotagging capabilities and reverse geocoding.</p>
        <br>
        <p><b>Features:</b></p>
        <ul>
            <li>Interactive map with GPS coordinate management</li>
            <li>Reverse geocoding using OpenStreetMap Nominatim</li>
            <li>Comprehensive metadata editing</li>
            <li>Batch operations support</li>
            <li>Timezone and date/time management</li>
            <li>Keywords auto-update with country information</li>
        </ul>
        <br>
        <p><b>Built with:</b> PySide6, ExifTool, OpenStreetMap, Leaflet</p>
        <p><b>License:</b> Apache 2.0</p>
        """
        
        QMessageBox.about(self, "About GeoSetter Lite", about_text)
    
    def load_images(self):
        """Load images from the directory"""
        self.statusBar().showMessage("Loading images...")
        
        # Create file scanner
        scanner = FileScanner(self.exiftool_service)
        
        # Scan directory
        self.images = scanner.scan_directory(self.directory)
        
        # Populate table
        self.populate_table()
        
        # Update map with all images that have GPS coordinates
        self.update_all_images_on_map()
        
        self.statusBar().showMessage(f"Loaded {len(self.images)} images")
    
    def populate_table(self):
        """Populate the table with image data"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.images))
        
        # Block signals during table population to avoid triggering on_item_changed
        self.table.blockSignals(True)
        
        for row, image in enumerate(self.images):
            # Filename (0)
            filename_item = QTableWidgetItem(image.filename)
            filename_item.setData(Qt.ItemDataRole.UserRole, image)
            filename_item.setFlags(filename_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, filename_item)
            
            # Taken Date (1) - editable with date picker
            taken_date_str = format_date(image.taken_date) if image.taken_date else ""
            taken_date_item = QTableWidgetItem(taken_date_str)
            taken_date_item.setFlags(taken_date_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, taken_date_item)
            
            # TZ Offset (2) - editable with dropdown
            tz_offset_item = QTableWidgetItem(image.tz_offset or "")
            tz_offset_item.setFlags(tz_offset_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, tz_offset_item)
            
            # GPS Coordinates (3) - editable
            gps_item = QTableWidgetItem(
                format_gps_coordinates(image.gps_latitude, image.gps_longitude)
            )
            gps_item.setFlags(gps_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, gps_item)
            
            # City (4) - editable
            city_item = QTableWidgetItem(image.city or "")
            city_item.setFlags(city_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, city_item)
            
            # Sublocation (5) - editable
            sublocation_item = QTableWidgetItem(image.sublocation or "")
            sublocation_item.setFlags(sublocation_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, sublocation_item)
            
            # Headline (6) - editable
            headline_item = QTableWidgetItem(image.headline or "")
            headline_item.setFlags(headline_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 6, headline_item)
            
            # Camera Model (7) - editable
            camera_item = QTableWidgetItem(image.camera_model or "")
            camera_item.setFlags(camera_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 7, camera_item)
            
            # Size (8)
            size_item = QTableWidgetItem(format_file_size(image.size))
            self.table.setItem(row, 8, size_item)
            
            # GPS Date (9) - editable with date picker
            gps_date_str = format_date(image.gps_date) if image.gps_date else ""
            gps_date_item = QTableWidgetItem(gps_date_str)
            gps_date_item.setFlags(gps_date_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 9, gps_date_item)
            
            # Country (10) - editable with dropdown
            country_item = QTableWidgetItem(image.country or "")
            country_item.setFlags(country_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 10, country_item)
            
            # Keywords (11) - editable, semicolon-separated for display
            keywords_str = "; ".join(image.keywords) if image.keywords else ""
            keywords_item = QTableWidgetItem(keywords_str)
            keywords_item.setFlags(keywords_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 11, keywords_item)
            
            # Created Date (12) - editable with date picker
            created_date_str = format_date(image.created_date) if image.created_date else ""
            created_date_item = QTableWidgetItem(created_date_str)
            created_date_item.setFlags(created_date_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 12, created_date_item)
        
        # Unblock signals after population is complete
        self.table.blockSignals(False)
        
        self.table.setSortingEnabled(True)
    
    def on_selection_changed(self):
        """Handle selection change in the table"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if selected_rows:
            # Get the first selected row for image display
            row = selected_rows[0].row()
            item = self.table.item(row, 0)
            
            if item:
                image = item.data(Qt.ItemDataRole.UserRole)
                if image:
                    self.display_image(image)
            
            # Update map to highlight selected images
            self.update_all_images_on_map()
            
            # Enable/disable set marker action based on whether selected image has GPS
            has_gps = False
            if len(selected_rows) == 1:
                item = self.table.item(selected_rows[0].row(), 0)
                if item:
                    image = item.data(Qt.ItemDataRole.UserRole)
                    if image and image.gps_latitude is not None and image.gps_longitude is not None:
                        has_gps = True
            
            self.map_panel.enable_set_marker_action(has_gps)
            
            # Enable repair action if any images are selected
            self.map_panel.enable_repair_action(len(selected_rows) > 0)
            
            # Check if any selected image needs Taken Date or GPS Date
            needs_taken_date = False
            needs_gps_date = False
            for row in selected_rows:
                item = self.table.item(row.row(), 0)
                if item:
                    image = item.data(Qt.ItemDataRole.UserRole)
                    if image:
                        if not image.taken_date:
                            needs_taken_date = True
                        if image.taken_date and not image.gps_date:
                            needs_gps_date = True
            
            self.map_panel.enable_set_taken_date_action(needs_taken_date)
            self.map_panel.enable_set_gps_date_action(needs_gps_date)
            
            # Enable batch edit only when more than one image is selected
            self.map_panel.enable_batch_edit_action(len(selected_rows) > 1)
            
            # Enable update GPS button if active marker exists and images are selected
            active_marker = self.map_panel.map_widget.get_active_marker()
            self.map_panel.enable_update_coords_action(active_marker is not None)
        else:
            # Still show all images on map, just none selected
            self.update_all_images_on_map()
            self.map_panel.enable_set_marker_action(False)
            self.map_panel.enable_repair_action(False)
            self.map_panel.enable_batch_edit_action(False)
            self.map_panel.enable_set_taken_date_action(False)
            self.map_panel.enable_set_gps_date_action(False)
            # Disable update GPS button when no selection
            self.map_panel.enable_update_coords_action(False)
    
    def update_keywords_with_country(self, row: int, country_name: str, country_code: str):
        """
        Update keywords to include country name and country code
        
        Args:
            row: Row index in the table
            country_name: Country name to add
            country_code: Country code to add
        """
        # Get current keywords
        keywords_item = self.table.item(row, 11)  # Keywords column is now at index 11
        if not keywords_item:
            return
        
        current_keywords_str = keywords_item.text().strip()
        # Parse semicolon-separated keywords (display format)
        keywords_list = [k.strip() for k in current_keywords_str.split(';') if k.strip()] if current_keywords_str else []
        
        # Add country code and country name if not already present
        if country_code and country_code not in keywords_list:
            keywords_list.append(country_code)
        if country_name and country_name not in keywords_list:
            keywords_list.append(country_name)
        
        # Update the keywords column (display with semicolon separator)
        new_keywords_str = "; ".join(keywords_list)
        keywords_item.setText(new_keywords_str)
        
        # Get the image and update metadata
        filename_item = self.table.item(row, 0)
        if filename_item:
            image = filename_item.data(Qt.ItemDataRole.UserRole)
            if image:
                try:
                    # Write as string with * separator (storage format)
                    keywords_storage_str = '*'.join(keywords_list)
                    metadata = {
                        'IPTC:Keywords': keywords_storage_str,
                        'XMP-dc:Subject': keywords_storage_str
                    }
                    self.exiftool_service.write_metadata([image.filepath], metadata)
                    image.keywords = keywords_list
                    if not image.metadata:
                        image.metadata = {}
                    image.metadata['IPTC:Keywords'] = keywords_storage_str
                    image.metadata['XMP-dc:Subject'] = keywords_storage_str
                except Exception as e:
                    self.statusBar().showMessage(f"Error updating keywords: {e}")
    
    def on_item_changed(self, item: QTableWidgetItem):
        """Handle changes to editable table items"""
        # Temporarily block signals to prevent recursion
        self.table.blockSignals(True)
        
        try:
            row = item.row()
            col = item.column()
            new_value = item.text().strip()
            
            # Get the image for this row
            filename_item = self.table.item(row, 0)
            if not filename_item:
                return
            
            image = filename_item.data(Qt.ItemDataRole.UserRole)
            if not image:
                return
            
            # Handle filename column (column 0)
            if col == 0:
                # Filename cannot be empty
                if not new_value:
                    # Revert to original filename
                    item.setText(image.filename)
                    self.statusBar().showMessage("Filename cannot be empty")
                    return
                
                # If filename changed, rename the file
                if new_value != image.filename:
                    try:
                        old_path = image.filepath
                        new_path = old_path.parent / new_value
                        
                        # Check if new filename already exists
                        if new_path.exists():
                            QMessageBox.warning(
                                self,
                                "File Exists",
                                f"A file named '{new_value}' already exists in this directory."
                            )
                            # Revert to original filename
                            item.setText(image.filename)
                            return
                        
                        # Rename the file
                        old_path.rename(new_path)
                        
                        # Check if ExifTool backup exists and rename it too
                        old_backup_path = old_path.parent / (old_path.name + "_original")
                        if old_backup_path.exists():
                            new_backup_path = new_path.parent / (new_path.name + "_original")
                            try:
                                old_backup_path.rename(new_backup_path)
                            except Exception as backup_error:
                                # Log warning but don't fail the rename operation
                                print(f"Warning: Could not rename backup file: {backup_error}")
                        
                        # Update image model
                        image.filename = new_value
                        image.filepath = new_path
                        
                        self.statusBar().showMessage(f"Renamed file to {new_value}")
                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            "Rename Failed",
                            f"Failed to rename file: {str(e)}"
                        )
                        # Revert to original filename
                        item.setText(image.filename)
                return
            
            # Determine which field was edited and save to file
            metadata = {}
            field_name = None
            
            if col == 2:  # TZ Offset
                field_name = 'tz_offset'
                # TZ Offset should be in "+HH:MM" format
                # Write to multiple offset tags with proper formats
                if new_value:
                    try:
                        # Parse "+05:00" or "-04:30" format
                        sign = 1 if new_value[0] == '+' else -1
                        hours = int(new_value[1:3])
                        minutes = int(new_value[4:6])
                        # TimeZoneOffset is in hours (can be fractional)
                        tz_offset_hours = sign * (hours + minutes / 60.0)
                        
                        metadata['EXIF:TimeZoneOffset'] = str(tz_offset_hours)
                        metadata['EXIF:OffsetTime'] = new_value
                        metadata['EXIF:OffsetTimeOriginal'] = new_value
                        metadata['EXIF:OffsetTimeDigitized'] = new_value
                    except (ValueError, IndexError):
                        # If parsing fails, don't write anything
                        return
            elif col == 3:  # GPS Coordinates
                # Parse GPS coordinates in various formats or empty to clear
                if new_value.strip():
                    try:
                        # Remove degree symbols
                        coord_str = new_value.replace('°', '')
                        
                        # Split by comma
                        parts = coord_str.split(',')
                        if len(parts) == 2:
                            # Parse latitude (may have N/S suffix)
                            lat_str = parts[0].strip()
                            lat_multiplier = 1
                            if lat_str.endswith((' N', ' S')):
                                lat_multiplier = 1 if lat_str.endswith('N') else -1
                                lat_str = lat_str[:-2].strip()
                            lat = float(lat_str) * lat_multiplier
                            
                            # Parse longitude (may have E/W suffix)
                            lon_str = parts[1].strip()
                            lon_multiplier = 1
                            if lon_str.endswith((' E', ' W')):
                                lon_multiplier = 1 if lon_str.endswith('E') else -1
                                lon_str = lon_str[:-2].strip()
                            lon = float(lon_str) * lon_multiplier
                            
                            # Validate ranges
                            if -90 <= lat <= 90 and -180 <= lon <= 180:
                                metadata['EXIF:GPSLatitude'] = str(lat)
                                metadata['EXIF:GPSLongitude'] = str(lon)
                                
                                # Update image model
                                image.gps_latitude = lat
                                image.gps_longitude = lon
                            else:
                                QMessageBox.warning(
                                    self,
                                    "Invalid Coordinates",
                                    "Latitude must be between -90 and 90, Longitude between -180 and 180."
                                )
                                return
                        else:
                            QMessageBox.warning(
                                self,
                                "Invalid Format",
                                "GPS coordinates must be in format: latitude, longitude (e.g., 48.856614, 2.352222 or 48.856614° N, 2.352222° E)"
                            )
                            return
                    except ValueError:
                        QMessageBox.warning(
                            self,
                            "Invalid Format",
                            "GPS coordinates must be numeric values (e.g., 48.856614, 2.352222)"
                        )
                        return
                else:
                    # Clear GPS coordinates
                    metadata['EXIF:GPSLatitude'] = ''
                    metadata['EXIF:GPSLongitude'] = ''
                    image.gps_latitude = None
                    image.gps_longitude = None
                
                # Write metadata
                try:
                    self.exiftool_service.write_metadata([image.filepath], metadata)
                    # Update map to reflect changes
                    self.update_all_images_on_map()
                    self.statusBar().showMessage(f"Updated GPS coordinates for {image.filename}")
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to update GPS coordinates: {str(e)}"
                    )
                return  # GPS coordinates handled separately
            elif col == 4:  # City
                field_name = 'city'
                metadata['IPTC:City'] = new_value
                metadata['XMP-photoshop:City'] = new_value
            elif col == 5:  # Sublocation
                field_name = 'sublocation'
                metadata['IPTC:Sub-location'] = new_value
                metadata['XMP-iptcCore:Location'] = new_value
            elif col == 6:  # Headline
                field_name = 'headline'
                metadata['IPTC:Headline'] = new_value
                metadata['XMP-photoshop:Headline'] = new_value
            elif col == 7:  # Camera Model
                field_name = 'camera_model'
                metadata['EXIF:Model'] = new_value
            elif col == 11:  # Keywords
                field_name = 'keywords'
                # Parse semicolon-separated keywords (display format)
                keywords_list = [k.strip() for k in new_value.split(';') if k.strip()]
                # Write as string with * separator (storage format)
                # If empty, write empty string to clear the keywords
                if keywords_list:
                    keywords_str = '*'.join(keywords_list)
                    metadata['IPTC:Keywords'] = keywords_str
                    metadata['XMP-dc:Subject'] = keywords_str
                else:
                    # Clear keywords by writing empty string
                    metadata['IPTC:Keywords'] = ''
                    metadata['XMP-dc:Subject'] = ''
            else:
                # Other columns are handled by delegates (dates, country) or are not editable
                return
            
            # Write to file
            try:
                self.exiftool_service.write_metadata([image.filepath], metadata)
                # Update image model
                if field_name == 'keywords':
                    # For keywords, store as list
                    image.keywords = keywords_list
                else:
                    setattr(image, field_name, new_value if new_value else None)
                
                if not image.metadata:
                    image.metadata = {}
                for tag, value in metadata.items():
                    image.metadata[tag] = value
                self.statusBar().showMessage(f"Updated {field_name.replace('_', ' ')} for {image.filename}")
            except Exception as e:
                self.statusBar().showMessage(f"Error updating {field_name}: {e}")
                # Revert the change in the UI
                old_value = getattr(image, field_name, "")
                item.setText(old_value or "")
        
        finally:
            self.table.blockSignals(False)
    
    def display_image(self, image: ImageModel):
        """
        Display an image in the viewer
        
        Args:
            image: ImageModel to display
        """
        self.current_image = image
        
        try:
            # Load image using PIL
            pil_image = Image.open(image.filepath)
            
            # Convert to RGB if necessary
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Get viewer size
            viewer_size = self.image_viewer.size()
            max_width = max(viewer_size.width() - 20, 1)  # Ensure at least 1 pixel
            max_height = max(viewer_size.height() - 20, 1)  # Ensure at least 1 pixel
            
            # Calculate scaled size maintaining aspect ratio
            img_width, img_height = pil_image.size
            
            # Only resize if image dimensions are valid
            if img_width > 0 and img_height > 0:
                scale = min(max_width / img_width, max_height / img_height, 1.0)
                
                if scale < 1.0:
                    new_width = max(int(img_width * scale), 1)  # Ensure at least 1 pixel
                    new_height = max(int(img_height * scale), 1)  # Ensure at least 1 pixel
                    pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert PIL Image to QPixmap directly (no temp file needed)
            # Convert PIL Image to bytes
            img_byte_array = io.BytesIO()
            pil_image.save(img_byte_array, format='PNG')
            img_byte_array.seek(0)
            
            # Load into QImage and convert to QPixmap
            qimage = QImage.fromData(img_byte_array.read())
            pixmap = QPixmap.fromImage(qimage)
            
            self.image_viewer.setPixmap(pixmap)
            self.statusBar().showMessage(f"Displaying: {image.filename}")
            
        except Exception as e:
            self.image_viewer.setText(f"Error loading image:\n{str(e)}")
            self.statusBar().showMessage(f"Error loading {image.filename}")
    
    def show_context_menu(self, position):
        """
        Show context menu for the table
        
        Args:
            position: Position where the context menu should appear
        """
        # Check if any rows are selected
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            return
        
        # Create context menu
        menu = QMenu(self)
        
        edit_action = QAction("Edit metadata", self)
        edit_action.triggered.connect(self.edit_metadata)
        menu.addAction(edit_action)
        
        # Show menu at cursor position
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def edit_metadata(self):
        """Open metadata editor for selected images"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            return
        
        # Get selected images
        selected_images = []
        for row in selected_rows:
            item = self.table.item(row.row(), 0)
            if item:
                image = item.data(Qt.ItemDataRole.UserRole)
                if image:
                    selected_images.append(image)
        
        if not selected_images:
            return
        
        # Get file paths
        filepaths = [img.filepath for img in selected_images]
        
        # Open metadata editor
        editor = MetadataEditor(filepaths, self.exiftool_service, self)
        result = editor.exec()
        
        # Reload images if changes were applied
        if result == QDialog.DialogCode.Accepted:
            self.reload_images()
    
    def batch_edit_metadata(self):
        """Open batch editor for selected images"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if len(selected_rows) < 2:
            QMessageBox.information(
                self,
                "Selection Required",
                "Please select at least 2 images for batch editing."
            )
            return
        
        # Get selected images
        selected_images = []
        for row in selected_rows:
            item = self.table.item(row.row(), 0)
            if item:
                image = item.data(Qt.ItemDataRole.UserRole)
                if image:
                    selected_images.append((row.row(), image))
        
        if not selected_images:
            return
        
        # Open batch edit dialog
        dialog = BatchEditDialog(len(selected_images), self)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # Get values from dialog
            values = dialog.get_values()
            
            # Prepare metadata updates
            metadata = {}
            
            # TZ Offset
            tz_offset = values.get('tz_offset', '').strip()
            if tz_offset:
                try:
                    # Parse "+05:00" or "-04:30" format
                    sign = 1 if tz_offset[0] == '+' else -1
                    hours = int(tz_offset[1:3])
                    minutes = int(tz_offset[4:6])
                    # TimeZoneOffset is in hours (can be fractional)
                    tz_offset_hours = sign * (hours + minutes / 60.0)
                    
                    metadata['EXIF:TimeZoneOffset'] = str(tz_offset_hours)
                    metadata['EXIF:OffsetTime'] = tz_offset
                    metadata['EXIF:OffsetTimeOriginal'] = tz_offset
                    metadata['EXIF:OffsetTimeDigitized'] = tz_offset
                except (ValueError, IndexError):
                    pass
            
            # Country
            country = values.get('country', '').strip()
            country_name = None
            if country:
                # Assuming country is ISO code, need to get country name
                from .table_delegates import CountryDelegate
                for code, name in CountryDelegate.COUNTRY_LIST:
                    if code == country:
                        country_name = name
                        break
                
                if country_name:
                    metadata['XMP-photoshop:Country'] = country_name
                    metadata['IPTC:Country-PrimaryLocationName'] = country_name
                    metadata['XMP-iptcCore:CountryCode'] = country
                    metadata['IPTC:Country-PrimaryLocationCode'] = country
            
            # City
            city = values.get('city', '').strip()
            if city:
                metadata['IPTC:City'] = city
                metadata['XMP-photoshop:City'] = city
            
            # Headline
            headline = values.get('headline', '').strip()
            if headline:
                metadata['IPTC:Headline'] = headline
                metadata['XMP-photoshop:Headline'] = headline
            
            if not metadata:
                return
            
            try:
                # If TZ Offset is being updated, we need to handle each image individually
                # to recalculate GPS Date and update XMP date tags
                if tz_offset:
                    for row, image in selected_images:
                        # Start with base metadata
                        image_metadata = {}
                        
                        # Add TZ Offset metadata
                        try:
                            sign = 1 if tz_offset[0] == '+' else -1
                            hours = int(tz_offset[1:3])
                            minutes = int(tz_offset[4:6])
                            tz_offset_hours = sign * (hours + minutes / 60.0)
                            
                            image_metadata['EXIF:TimeZoneOffset'] = str(tz_offset_hours)
                            image_metadata['EXIF:OffsetTime'] = tz_offset
                            image_metadata['EXIF:OffsetTimeOriginal'] = tz_offset
                            image_metadata['EXIF:OffsetTimeDigitized'] = tz_offset
                        except (ValueError, IndexError):
                            pass
                        
                        # Update XMP date tags with timezone offset
                        if image.taken_date:
                            taken_date_str = image.taken_date.strftime('%Y:%m:%d %H:%M:%S')
                            image_metadata['XMP-exif:DateTimeOriginal'] = taken_date_str + tz_offset
                        
                        if image.created_date:
                            created_date_str = image.created_date.strftime('%Y:%m:%d %H:%M:%S')
                            image_metadata['XMP-exif:DateTimeDigitized'] = created_date_str + tz_offset
                        
                        # Recalculate GPS Date in UTC ONLY if both taken_date and gps_date already exist
                        if image.taken_date and image.gps_date:
                            try:
                                from datetime import timedelta
                                sign = 1 if tz_offset[0] == '+' else -1
                                hours = int(tz_offset[1:3])
                                minutes = int(tz_offset[4:6])
                                offset_seconds = sign * (hours * 3600 + minutes * 60)
                                
                                # Convert to UTC by subtracting the offset
                                gps_utc = image.taken_date - timedelta(seconds=offset_seconds)
                                
                                gps_date_str = gps_utc.strftime('%Y:%m:%d')
                                gps_time_str = gps_utc.strftime('%H:%M:%S')
                                image_metadata['EXIF:GPSDateStamp'] = gps_date_str
                                image_metadata['EXIF:GPSTimeStamp'] = gps_time_str
                                
                                # Update image model
                                image.gps_date = gps_utc
                            except (ValueError, IndexError):
                                pass
                        
                        # Add other metadata (country, city, headline)
                        if country_name:
                            image_metadata['XMP-photoshop:Country'] = country_name
                            image_metadata['IPTC:Country-PrimaryLocationName'] = country_name
                            image_metadata['XMP-iptcCore:CountryCode'] = country
                            image_metadata['IPTC:Country-PrimaryLocationCode'] = country
                        
                        if city:
                            image_metadata['IPTC:City'] = city
                            image_metadata['XMP-photoshop:City'] = city
                        
                        if headline:
                            image_metadata['IPTC:Headline'] = headline
                            image_metadata['XMP-photoshop:Headline'] = headline
                        
                        # Write metadata for this image
                        self.exiftool_service.write_metadata([image.filepath], image_metadata)
                        
                        # Read Composite:GPSDateTime and write to XMP-exif:GPSDateTime if GPS date was updated
                        if image.taken_date and image.gps_date:
                            try:
                                file_metadata = self.exiftool_service.read_metadata(image.filepath)
                                composite_gps = file_metadata.get('Composite:GPSDateTime')
                                if composite_gps:
                                    self.exiftool_service.write_metadata(
                                        [image.filepath],
                                        {'XMP-exif:GPSDateTime': composite_gps}
                                    )
                            except Exception:
                                pass
                else:
                    # No TZ Offset update, write all metadata at once
                    filepaths = [img.filepath for _, img in selected_images]
                    self.exiftool_service.write_metadata(filepaths, metadata)
                
                # Update UI
                self.table.blockSignals(True)
                for row, image in selected_images:
                    # Update TZ Offset
                    if tz_offset:
                        image.tz_offset = tz_offset
                        item = self.table.item(row, 2)
                        if item:
                            item.setText(tz_offset)
                        
                        # Update GPS Date display if it was recalculated
                        if image.gps_date:
                            gps_date_item = self.table.item(row, 9)
                            if gps_date_item:
                                from .utils import format_date
                                gps_date_item.setText(format_date(image.gps_date))
                    
                    # Update Country
                    if country:
                        image.country = country
                        item = self.table.item(row, 10)
                        if item:
                            item.setText(country)
                        
                        # Update keywords with country info if country_name exists
                        if country_name:
                            self.update_keywords_with_country(row, country_name, country)
                    
                    # Update City
                    if city:
                        image.city = city
                        item = self.table.item(row, 4)
                        if item:
                            item.setText(city)
                    
                    # Update Headline
                    if headline:
                        image.headline = headline
                        item = self.table.item(row, 6)
                        if item:
                            item.setText(headline)
                
                self.table.blockSignals(False)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Metadata updated for {len(selected_images)} image(s)."
                )
                
                self.statusBar().showMessage(
                    f"Batch updated metadata for {len(selected_images)} image(s)"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to update metadata: {str(e)}"
                )
    
    def update_all_images_on_map(self):
        """Update map with markers for all images, highlighting selected ones"""
        selected_rows = self.table.selectionModel().selectedRows()
        selected_filenames = set()
        
        for row in selected_rows:
            item = self.table.item(row.row(), 0)
            if item:
                image = item.data(Qt.ItemDataRole.UserRole)
                if image:
                    selected_filenames.add(image.filename)
        
        # Create markers for all images with GPS coordinates
        markers = []
        for image in self.images:
            if image.gps_latitude is not None and image.gps_longitude is not None:
                is_selected = image.filename in selected_filenames
                markers.append((
                    image.gps_latitude,
                    image.gps_longitude,
                    image.filename,
                    is_selected,
                    str(image.filepath)  # Add filepath for thumbnail generation
                ))
        
        # Update map with markers
        self.map_panel.map_widget.update_markers(markers)
    
    def on_map_clicked(self, lat: float, lng: float):
        """Handle map click - enable update button only if images are selected"""
        selected_rows = self.table.selectionModel().selectedRows()
        # Only enable update button if there are selected images
        if selected_rows:
            self.map_panel.enable_update_coords_action(True)
        else:
            self.map_panel.enable_update_coords_action(False)
    
    def set_marker_from_selected_image(self):
        """Set active marker from the selected image's GPS coordinates"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if len(selected_rows) != 1:
            QMessageBox.warning(
                self,
                "Selection Error",
                "Please select exactly one image with GPS coordinates."
            )
            return
        
        item = self.table.item(selected_rows[0].row(), 0)
        if item:
            image = item.data(Qt.ItemDataRole.UserRole)
            if image and image.gps_latitude is not None and image.gps_longitude is not None:
                self.map_panel.map_widget.set_active_marker(
                    image.gps_latitude,
                    image.gps_longitude
                )
                # Update the info label with the coordinates
                self.map_panel.info_label.setText(
                    f"Active: {image.gps_latitude:.6f}°, {image.gps_longitude:.6f}°"
                )
                self.map_panel.enable_update_coords_action(True)
                self.statusBar().showMessage(
                    f"Active marker set from {image.filename}: "
                    f"{image.gps_latitude:.6f}°, {image.gps_longitude:.6f}°"
                )
            else:
                QMessageBox.warning(
                    self,
                    "No GPS Data",
                    "Selected image does not have GPS coordinates."
                )
    
    def update_selected_images_gps(self):
        """Update selected images with GPS coordinates from active marker"""
        active_marker = self.map_panel.map_widget.get_active_marker()
        
        if not active_marker:
            QMessageBox.warning(
                self,
                "No Active Marker",
                "Please click on the map to set an active marker first."
            )
            return
        
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select one or more images to update."
            )
            return
        
        # Get selected images
        selected_images = []
        for row in selected_rows:
            item = self.table.item(row.row(), 0)
            if item:
                image = item.data(Qt.ItemDataRole.UserRole)
                if image:
                    selected_images.append(image)
        
        if not selected_images:
            return
        
        # Confirm action
        lat, lon = active_marker
        result = QMessageBox.question(
            self,
            "Update GPS Coordinates",
            f"Update GPS coordinates for {len(selected_images)} image(s) to:\n"
            f"Latitude: {lat:.6f}°\n"
            f"Longitude: {lon:.6f}°\n\n"
            f"This will modify the EXIF/XMP metadata of the selected images.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result != QMessageBox.StandardButton.Yes:
            return
        
        # Prepare GPS metadata
        metadata = {
            'EXIF:GPSLatitude': str(lat),
            'EXIF:GPSLongitude': str(lon)
        }
        
        # Initialize geocoding info as None
        geocoding_info = None
        
        # Check if reverse geocoding is enabled
        if self.map_panel.is_reverse_geocoding_enabled():
            # Perform reverse geocoding
            self.statusBar().showMessage("Performing reverse geocoding...")
            geocoding_result = self.reverse_geocoding_service.reverse_geocode(lat, lon)
            
            if geocoding_result:
                # Show dialog with results
                dialog = GeocodingDialog(
                    geocoding_result.country,
                    geocoding_result.city,
                    len(selected_images),
                    self
                )
                
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    # Get edited values
                    country, country_code, city = dialog.get_values()
                    
                    # Add location metadata if provided
                    if country:
                        metadata['XMP-photoshop:Country'] = country
                        metadata['IPTC:Country-PrimaryLocationName'] = country
                    
                    if country_code:
                        metadata['XMP-iptcCore:CountryCode'] = country_code
                        metadata['IPTC:Country-PrimaryLocationCode'] = country_code
                    
                    if city:
                        metadata['XMP-photoshop:City'] = city
                        metadata['IPTC:City'] = city
                    
                    # Store the country/city info to apply keywords later
                    geocoding_info = {
                        'country': country,
                        'country_code': country_code,
                        'city': city
                    }
                else:
                    # User cancelled the geocoding dialog
                    self.statusBar().showMessage("GPS update cancelled")
                    return
            else:
                # Reverse geocoding failed, ask user if they want to continue
                result = QMessageBox.question(
                    self,
                    "Reverse Geocoding Failed",
                    "Reverse geocoding failed to retrieve location information.\n\n"
                    "Do you want to continue updating GPS coordinates only?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if result != QMessageBox.StandardButton.Yes:
                    self.statusBar().showMessage("GPS update cancelled")
                    return
        
        # Update metadata
        try:
            # Check if we have geocoding info with keywords to update
            if geocoding_info is not None:
                country = geocoding_info.get('country')
                country_code = geocoding_info.get('country_code')
                
                # Update each image individually to handle keywords properly
                for image in selected_images:
                    # Start with base GPS metadata
                    image_metadata = metadata.copy()
                    
                    # Add keywords with country information if country data exists
                    if country or country_code:
                        # Get current keywords for this image
                        keywords_list = list(image.keywords) if image.keywords else []
                        
                        # Add country code and country name if not already present
                        if country_code and country_code not in keywords_list:
                            keywords_list.append(country_code)
                        if country and country not in keywords_list:
                            keywords_list.append(country)
                        
                        # Add keywords to metadata
                        if keywords_list:
                            keywords_str = '*'.join(keywords_list)
                            image_metadata['IPTC:Keywords'] = keywords_str
                            image_metadata['XMP-dc:Subject'] = keywords_str
                    
                    # Write metadata for this image
                    self.exiftool_service.write_metadata([image.filepath], image_metadata)
            else:
                # No geocoding or no keywords to update, write all at once
                filepaths = [img.filepath for img in selected_images]
                self.exiftool_service.write_metadata(filepaths, metadata)
            
            QMessageBox.information(
                self,
                "Success",
                f"GPS coordinates updated for {len(selected_images)} image(s)."
            )
            
            # Reload images
            self.reload_images()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update GPS coordinates: {str(e)}"
            )
    
    def repair_selected_images_metadata(self):
        """Repair/fix metadata for selected images"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select one or more images to repair metadata."
            )
            return
        
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Repair",
            f"This will repair metadata for {len(selected_rows)} selected image(s).\n\n"
            "The repair process will:\n"
            "- Remove all metadata\n"
            "- Copy it back from the original\n"
            "- Fix any corrupted structures\n"
            "- Preserve ICC profiles\n\n"
            "This operation cannot be undone. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Get selected images
        selected_images = []
        filepaths = []
        for row in selected_rows:
            item = self.table.item(row.row(), 0)
            if item:
                image = item.data(Qt.ItemDataRole.UserRole)
                if image:
                    selected_images.append(image)
                    filepaths.append(image.filepath)
        
        if not filepaths:
            return
        
        try:
            self.statusBar().showMessage(f"Repairing metadata for {len(filepaths)} image(s)...")
            
            # Repair metadata
            self.exiftool_service.repair_metadata(filepaths)
            
            QMessageBox.information(
                self,
                "Success",
                f"Metadata repaired successfully for {len(filepaths)} image(s)."
            )
            
            # Reload images
            self.reload_images()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to repair metadata: {str(e)}"
            )
    
    def set_taken_date_from_creation(self):
        """Set Taken Date from file creation date for selected images"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select one or more images to set Taken Date."
            )
            return
        
        # Get selected images without Taken Date
        images_to_update = []
        filepaths = []
        for row in selected_rows:
            item = self.table.item(row.row(), 0)
            if item:
                image = item.data(Qt.ItemDataRole.UserRole)
                if image and not image.taken_date and image.creation_date:
                    images_to_update.append(image)
                    filepaths.append(image.filepath)
        
        if not filepaths:
            QMessageBox.information(
                self,
                "No Images to Update",
                "All selected images already have Taken Date or no file creation date available."
            )
            return
        
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Set Taken Date",
            f"Set Taken Date from file creation date for {len(filepaths)} image(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self.statusBar().showMessage(f"Setting Taken Date for {len(filepaths)} image(s)...")
            
            # Write Taken Date for each image
            for image in images_to_update:
                taken_date_str = image.creation_date.strftime('%Y:%m:%d %H:%M:%S')
                # Concatenate timezone offset to XMP tag if available
                tz_offset = image.tz_offset or ""
                xmp_date_str = taken_date_str + tz_offset if tz_offset else taken_date_str
                metadata = {
                    'EXIF:DateTimeOriginal': taken_date_str,
                    'XMP-exif:DateTimeOriginal': xmp_date_str
                }
                self.exiftool_service.write_metadata([image.filepath], metadata)
            
            QMessageBox.information(
                self,
                "Success",
                f"Taken Date set successfully for {len(filepaths)} image(s)."
            )
            
            # Reload images
            self.reload_images()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to set Taken Date: {str(e)}"
            )
    
    def set_gps_date_from_taken(self):
        """Set GPS Date from Taken Date for selected images"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select one or more images to set GPS Date."
            )
            return
        
        # Get selected images with Taken Date but without GPS Date
        images_to_update = []
        filepaths = []
        for row in selected_rows:
            item = self.table.item(row.row(), 0)
            if item:
                image = item.data(Qt.ItemDataRole.UserRole)
                if image and image.taken_date and not image.gps_date:
                    images_to_update.append(image)
                    filepaths.append(image.filepath)
        
        if not filepaths:
            QMessageBox.information(
                self,
                "No Images to Update",
                "All selected images already have GPS Date or no Taken Date available."
            )
            return
        
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Set GPS Date",
            f"Set GPS Date from Taken Date for {len(filepaths)} image(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self.statusBar().showMessage(f"Setting GPS Date for {len(filepaths)} image(s)...")
            
            # Write GPS Date for each image (convert to UTC)
            for image in images_to_update:
                # Convert Taken Date (local time) to UTC using TZ Offset
                if image.tz_offset:
                    # Parse offset string
                    try:
                        from datetime import timedelta
                        sign = 1 if image.tz_offset[0] == '+' else -1
                        hours = int(image.tz_offset[1:3])
                        minutes = int(image.tz_offset[4:6])
                        offset_seconds = sign * (hours * 3600 + minutes * 60)
                        
                        # Convert to UTC by subtracting the offset
                        gps_utc = image.taken_date - timedelta(seconds=offset_seconds)
                    except (ValueError, IndexError):
                        # If offset parsing fails, use taken_date as-is
                        gps_utc = image.taken_date
                else:
                    # No offset, assume taken_date is already in UTC
                    gps_utc = image.taken_date
                
                gps_date_str = gps_utc.strftime('%Y:%m:%d')
                gps_time_str = gps_utc.strftime('%H:%M:%S')
                metadata = {
                    'EXIF:GPSDateStamp': gps_date_str,
                    'EXIF:GPSTimeStamp': gps_time_str
                }
                self.exiftool_service.write_metadata([image.filepath], metadata)
                
                # Read Composite:GPSDateTime and write to XMP-exif:GPSDateTime
                try:
                    file_metadata = self.exiftool_service.read_metadata(image.filepath)
                    composite_gps = file_metadata.get('Composite:GPSDateTime')
                    if composite_gps:
                        self.exiftool_service.write_metadata(
                            [image.filepath],
                            {'XMP-exif:GPSDateTime': composite_gps}
                        )
                except Exception:
                    pass  # Silently ignore if composite read/write fails
            
            QMessageBox.information(
                self,
                "Success",
                f"GPS Date set successfully for {len(filepaths)} image(s)."
            )
            
            # Reload images
            self.reload_images()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to set GPS Date: {str(e)}"
            )
    
    def eventFilter(self, obj, event):
        """Event filter to handle Delete/Backspace keys in table"""
        if obj == self.table and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if key_event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                # Get current item
                current_item = self.table.currentItem()
                if current_item:
                    col = current_item.column()
                    # Allow deletion for editable columns: Taken Date (1), TZ Offset (2), GPS Coordinates (3), City (4), Sublocation (5),
                    # Headline (6), Camera Model (7), GPS Date (9), Country (10), Keywords (11), Created Date (12)
                    if col in (1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12):
                        row = current_item.row()
                        filename_item = self.table.item(row, 0)
                        if filename_item:
                            image = filename_item.data(Qt.ItemDataRole.UserRole)
                            if image:
                                # Clear the value
                                current_item.setText("")
                                
                                # Determine which metadata tags to clear
                                tags_to_clear = []
                                field_name = None
                                
                                if col == 1:  # Taken Date
                                    tags_to_clear = ['EXIF:DateTimeOriginal', 'XMP-exif:DateTimeOriginal']
                                    field_name = 'taken_date'
                                elif col == 2:  # TZ Offset
                                    tags_to_clear = [
                                        'EXIF:TimeZoneOffset',
                                        'EXIF:OffsetTime',
                                        'EXIF:OffsetTimeOriginal',
                                        'EXIF:OffsetTimeDigitized'
                                    ]
                                    field_name = 'tz_offset'
                                elif col == 3:  # GPS Coordinates
                                    tags_to_clear = [
                                        'EXIF:GPSLatitude',
                                        'EXIF:GPSLongitude',
                                        'EXIF:GPSLatitudeRef',
                                        'EXIF:GPSLongitudeRef'
                                    ]
                                    field_name = 'gps_coordinates'
                                elif col == 4:  # City
                                    tags_to_clear = ['IPTC:City', 'XMP-photoshop:City']
                                    field_name = 'city'
                                elif col == 5:  # Sublocation
                                    tags_to_clear = ['IPTC:Sub-location', 'XMP-iptcCore:Location']
                                    field_name = 'sublocation'
                                elif col == 6:  # Headline
                                    tags_to_clear = ['IPTC:Headline', 'XMP-photoshop:Headline']
                                    field_name = 'headline'
                                elif col == 7:  # Camera Model
                                    tags_to_clear = ['EXIF:Model']
                                    field_name = 'camera_model'
                                elif col == 9:  # GPS Date
                                    tags_to_clear = ['EXIF:GPSDateStamp', 'EXIF:GPSTimeStamp']
                                    field_name = 'gps_date'
                                elif col == 10:  # Country
                                    tags_to_clear = [
                                        'XMP-photoshop:Country',
                                        'IPTC:Country-PrimaryLocationName',
                                        'XMP-iptcCore:CountryCode',
                                        'IPTC:Country-PrimaryLocationCode'
                                    ]
                                    field_name = 'country'
                                elif col == 11:  # Keywords
                                    tags_to_clear = ['IPTC:Keywords', 'XMP-dc:Subject']
                                    field_name = 'keywords'
                                elif col == 12:  # Created Date
                                    tags_to_clear = ['EXIF:CreateDate', 'XMP-exif:DateTimeDigitized']
                                    field_name = 'created_date'
                                else:
                                    return super().eventFilter(obj, event)
                                
                                # Clear from file
                                try:
                                    for tag in tags_to_clear:
                                        self.exiftool_service.delete_tag([image.filepath], tag)
                                    
                                    # Update image model
                                    if field_name == 'keywords':
                                        # For keywords, set to empty list
                                        image.keywords = []
                                    elif field_name == 'gps_coordinates':
                                        # For GPS coordinates, clear both lat and lon
                                        image.gps_latitude = None
                                        image.gps_longitude = None
                                        # Update map to remove marker
                                        self.update_all_images_on_map()
                                    else:
                                        setattr(image, field_name, None)
                                    
                                    for tag in tags_to_clear:
                                        if tag in image.metadata:
                                            del image.metadata[tag]
                                    
                                    self.statusBar().showMessage(f"Cleared {field_name.replace('_', ' ')} for {image.filename}")
                                except Exception as e:
                                    self.statusBar().showMessage(f"Error clearing {field_name}: {e}")
                                
                                return True  # Event handled
        
        return super().eventFilter(obj, event)
    
    def reload_images(self):
        """Reload images after metadata changes"""
        self.statusBar().showMessage("Reloading images...")
        
        # Remember current selection
        selected_filenames = []
        selected_rows = self.table.selectionModel().selectedRows()
        for row in selected_rows:
            item = self.table.item(row.row(), 0)
            if item:
                image = item.data(Qt.ItemDataRole.UserRole)
                if image:
                    selected_filenames.append(image.filename)
        
        # Reload images
        self.load_images()
        
        # Restore selection
        if selected_filenames:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item:
                    image = item.data(Qt.ItemDataRole.UserRole)
                    if image and image.filename in selected_filenames:
                        self.table.selectRow(row)
    
    def _create_recycle_bin_icon(self) -> QIcon:
        """Create a recycle bin icon for context menu"""
        # Create smaller pixmap for better alignment (16x16 is standard for menu icons)
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Use dark grey color for professional look
        dark_grey = QColor(80, 80, 80)
        light_grey = QColor(120, 120, 120)
        
        # Draw trash can body
        painter.setPen(QPen(dark_grey, 1.5))
        painter.setBrush(light_grey)
        painter.drawRect(4, 7, 8, 7)
        
        # Draw trash can lid
        painter.drawRect(3, 5, 10, 2)
        
        # Draw handle on lid
        painter.setPen(QPen(dark_grey, 1.5))
        painter.drawLine(6, 3, 6, 5)
        painter.drawLine(10, 3, 10, 5)
        
        # Draw vertical lines on trash can body
        painter.setPen(QPen(dark_grey, 1))
        painter.drawLine(6, 8, 6, 13)
        painter.drawLine(8, 8, 8, 13)
        painter.drawLine(10, 8, 10, 13)
        
        painter.end()
        
        # Create icon from pixmap
        icon = QIcon(pixmap)
        return icon
    
    def _setup_header_buttons(self):
        """Setup header context menu for clearing columns"""
        header = self.table.horizontalHeader()
        
        # Enable context menu on header
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_header_context_menu)
    
    def _show_header_context_menu(self, pos: QPoint):
        """Show context menu when right-clicking on header"""
        header = self.table.horizontalHeader()
        logical_index = header.logicalIndexAt(pos)
        
        # Check if column is clearable
        if self.column_metadata_map.get(logical_index) is None:
            return
        
        # Check if there are selected images
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        # Create context menu
        menu = QMenu(self)
        
        # Ensure icons are visible in menu (some platforms hide them by default)
        menu.setToolTipsVisible(True)
        
        # Add clear action with icon
        recycle_icon = self._create_recycle_bin_icon()
        column_name = self.table.horizontalHeaderItem(logical_index).text()
        clear_action = QAction(recycle_icon, f"Clear '{column_name}' for selected images", self)
        clear_action.setIconVisibleInMenu(True)  # Explicitly enable icon
        clear_action.triggered.connect(lambda: self._clear_column_with_confirmation(logical_index))
        menu.addAction(clear_action)
        
        # Show menu at cursor position
        menu.exec(header.mapToGlobal(pos))
    
    def _clear_column_with_confirmation(self, column: int):
        """Clear column with confirmation dialog"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        column_name = self.table.horizontalHeaderItem(column).text()
        result = QMessageBox.question(
            self,
            "Clear Column",
            f"Clear '{column_name}' for {len(selected_rows)} selected image(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            self._clear_column(column)
    
    def _clear_column(self, column: int):
        """Clear column content for selected images"""
        metadata_info = self.column_metadata_map.get(column)
        if metadata_info is None:
            return
        
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        tags_to_clear = metadata_info['tags']
        field_name = metadata_info['field']
        
        # Get selected images
        selected_images = []
        for row in selected_rows:
            item = self.table.item(row.row(), 0)
            if item:
                image = item.data(Qt.ItemDataRole.UserRole)
                if image:
                    selected_images.append((row.row(), image))
        
        if not selected_images:
            return
        
        try:
            # Delete tags from files
            filepaths = [img.filepath for _, img in selected_images]
            for tag in tags_to_clear:
                try:
                    self.exiftool_service.delete_tag(filepaths, tag)
                except Exception as e:
                    print(f"Warning: Could not delete tag {tag}: {e}")
            
            # Update UI and model
            self.table.blockSignals(True)
            for row, image in selected_images:
                # Clear the cell
                item = self.table.item(row, column)
                if item:
                    item.setText("")
                
                # Clear the model field
                if field_name == 'taken_date':
                    image.taken_date = None
                elif field_name == 'tz_offset':
                    image.tz_offset = None
                elif field_name == 'gps_coordinates':
                    image.gps_latitude = None
                    image.gps_longitude = None
                elif field_name == 'city':
                    image.city = None
                elif field_name == 'sublocation':
                    image.sublocation = None
                elif field_name == 'headline':
                    image.headline = None
                elif field_name == 'camera_model':
                    image.camera_model = None
                elif field_name == 'gps_date':
                    image.gps_date = None
                elif field_name == 'country':
                    image.country = None
                elif field_name == 'keywords':
                    image.keywords = []
                elif field_name == 'created_date':
                    image.created_date = None
            
            self.table.blockSignals(False)
            
            # Update map if GPS coordinates were cleared
            if field_name == 'gps_coordinates':
                self.update_all_images_on_map()
            
            column_name = self.table.horizontalHeaderItem(column).text()
            self.statusBar().showMessage(
                f"Cleared '{column_name}' for {len(selected_images)} image(s)"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to clear column: {str(e)}"
            )
        
        self.statusBar().showMessage("Images reloaded")
    
    def _find_similar_photos(self):
        """Find and display similar photos using AI"""
        if not self.images:
            QMessageBox.information(
                self,
                "No Images",
                "No images loaded. Please load a directory with images first."
            )
            return
        
        # Get AI settings
        ai_settings = Config.get_ai_settings()
        threshold = ai_settings['similarity_threshold']
        
        # Show progress dialog
        progress = ProgressDialog("Finding Similar Photos", self)
        progress.set_status("Initializing AI model...")
        progress.set_indeterminate(True)
        progress.show()
        
        # Process events to show the dialog
        from PySide6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        
        try:
            # Get all image paths
            image_paths = [img.filepath for img in self.images]
            
            # Set determinate progress
            progress.set_indeterminate(False)
            
            # Compute similarity
            def progress_callback(current, total):
                if progress.is_cancelled():
                    return
                progress.set_progress(current, total)
                QCoreApplication.processEvents()
            
            similarity_groups = self.ai_service.compute_similarity(
                image_paths,
                threshold,
                progress_callback
            )
            
            # Close progress dialog
            progress.close()
            
            if progress.is_cancelled():
                self.statusBar().showMessage("Similarity search cancelled")
                return
            
            # Show results dialog
            if similarity_groups:
                dialog = SimilarityDialog(similarity_groups, self)
                dialog.images_deleted.connect(self._on_images_deleted)
                dialog.exec()
            else:
                QMessageBox.information(
                    self,
                    "No Similar Photos",
                    f"No similar photos found with threshold {threshold:.0%}.\n\n"
                    "Try lowering the similarity threshold in AI Tools > Settings."
                )
        
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to find similar photos:\n{str(e)}"
            )
    
    def _predict_locations(self):
        """Predict GPS locations for images without coordinates"""
        if not self.images:
            QMessageBox.information(
                self,
                "No Images",
                "No images loaded. Please load a directory with images first."
            )
            return
        
        # Find images without GPS coordinates
        images_without_gps = [
            img for img in self.images 
            if img.gps_latitude is None or img.gps_longitude is None
        ]
        
        if not images_without_gps:
            QMessageBox.information(
                self,
                "All Images Have GPS",
                "All loaded images already have GPS coordinates."
            )
            return
        
        # Show progress dialog
        progress = ProgressDialog("Predicting Locations", self)
        progress.set_status("Initializing AI model...")
        progress.set_indeterminate(True)
        progress.show()
        
        # Process events to show the dialog
        from PySide6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        
        try:
            # Set determinate progress
            progress.set_indeterminate(False)
            
            # Predict locations for each image
            predictions = {}
            for i, image in enumerate(images_without_gps):
                if progress.is_cancelled():
                    break
                
                progress.set_progress(i, len(images_without_gps))
                progress.set_detail(f"Analyzing {image.filepath.name}...")
                QCoreApplication.processEvents()
                
                location_list = self.ai_service.predict_location(image.filepath, top_k=5)
                if location_list:
                    predictions[image.filepath] = location_list
            
            # Close progress dialog
            progress.close()
            
            if progress.is_cancelled():
                self.statusBar().showMessage("Location prediction cancelled")
                return
            
            # Show results dialog
            if predictions:
                dialog = GeolocationDialog(predictions, self)
                dialog.locations_applied.connect(self._on_locations_applied)
                dialog.exec()
            else:
                QMessageBox.warning(
                    self,
                    "No Predictions",
                    "Could not predict locations for any images.\n\n"
                    "This may happen if the images are too abstract or don't contain "
                    "recognizable geographic features."
                )
        
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to predict locations:\n{str(e)}"
            )
    
    def _show_ai_settings(self):
        """Show AI settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload AI service with new settings
            ai_settings = Config.get_ai_settings()
            self.ai_service = AIService(ai_settings['model_cache_dir'])
            self.statusBar().showMessage("AI settings updated")
    
    def _on_images_deleted(self, deleted_paths):
        """Handle images deleted from similarity dialog"""
        # Remove deleted images from the list
        self.images = [img for img in self.images if img.filepath not in deleted_paths]
        
        # Refresh the table
        self.populate_table()
        
        # Update map
        self.update_all_images_on_map()
        
        self.statusBar().showMessage(f"Deleted {len(deleted_paths)} image(s)")
    
    def _on_locations_applied(self, locations_dict):
        """Handle locations applied from geolocation dialog"""
        count = 0
        for image_path, (lat, lon) in locations_dict.items():
            # Find the image in our list
            for image in self.images:
                if image.filepath == image_path:
                    # Write GPS coordinates to metadata
                    self.exiftool_service.write_metadata(
                        image_path,
                        {
                            'EXIF:GPSLatitude': abs(lat),
                            'EXIF:GPSLatitudeRef': 'N' if lat >= 0 else 'S',
                            'EXIF:GPSLongitude': abs(lon),
                            'EXIF:GPSLongitudeRef': 'E' if lon >= 0 else 'W',
                        }
                    )
                    
                    # Update image model
                    image.gps_latitude = lat
                    image.gps_longitude = lon
                    count += 1
                    break
        
        # Refresh the table
        self.populate_table()
        
        # Update map
        self.update_all_images_on_map()
        
        self.statusBar().showMessage(f"Applied GPS coordinates to {count} image(s)")

