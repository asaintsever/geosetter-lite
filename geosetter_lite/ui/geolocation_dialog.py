"""Dialog for displaying and managing geolocation predictions"""

from pathlib import Path
from typing import List, Tuple, Optional, Dict
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QRadioButton, QButtonGroup,
    QWidget, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PIL import Image
import io

from ..services.reverse_geocoding_service import ReverseGeocodingService


class GeolocationDialog(QDialog):
    """Dialog showing geolocation predictions for images"""
    
    locations_applied = Signal(dict)  # Emits dict of {image_path: {'lat': lat, 'lon': lon, 'country': country, 'city': city}}
    
    def __init__(
        self, 
        predictions: Dict[Path, List[Tuple[float, float, float]]], 
        parent=None
    ):
        """Initialize geolocation dialog
        
        Args:
            predictions: Dict mapping image paths to list of (lat, lon, confidence) tuples
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Geolocation Predictions")
        self.setModal(True)
        self.setMinimumSize(900, 600)
        
        self.predictions = predictions
        self.selected_locations: Dict[Path, Tuple[float, float]] = {}
        self.location_names: Dict[Tuple[float, float], str] = {}
        self.location_info: Dict[Tuple[float, float], Dict[str, Optional[str]]] = {}  # Store full geocoding results
        self.reverse_geocoding = ReverseGeocodingService()
        
        self.init_ui()
        
        # Start reverse geocoding for predictions
        self._reverse_geocode_predictions()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Header
        if not self.predictions:
            header_label = QLabel("No images without GPS coordinates found.")
            header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(header_label)
            
            close_button = QPushButton("Close")
            close_button.clicked.connect(self.reject)
            layout.addWidget(close_button)
            return
        
        header_label = QLabel(
            f"Predicted locations for {len(self.predictions)} image(s) without GPS coordinates:"
        )
        header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header_label)
        
        info_label = QLabel(
            "Select a predicted location for each image. "
            "Location names are being fetched..."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(info_label)
        
        # Table for predictions
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Image", "Filename", "Predicted Locations"])
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 200)
        
        # Populate table
        self.table.setRowCount(len(self.predictions))
        for row, (image_path, location_list) in enumerate(self.predictions.items()):
            self._populate_row(row, image_path, location_list)
        
        layout.addWidget(self.table)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        button_layout.addStretch()
        
        apply_button = QPushButton("Apply Selected")
        apply_button.clicked.connect(self._apply_selected)
        button_layout.addWidget(apply_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def _populate_row(
        self, 
        row: int, 
        image_path: Path, 
        location_list: List[Tuple[float, float, float]]
    ):
        """Populate a table row with image and predictions
        
        Args:
            row: Row index
            image_path: Path to the image
            location_list: List of (lat, lon, confidence) tuples
        """
        # Thumbnail
        thumbnail_label = QLabel()
        thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail_label.setFixedSize(80, 80)
        
        try:
            pixmap = self._load_thumbnail(image_path, 80, 80)
            thumbnail_label.setPixmap(pixmap)
        except Exception as e:
            thumbnail_label.setText("No preview")
            print(f"Error loading thumbnail for {image_path}: {e}")
        
        self.table.setCellWidget(row, 0, thumbnail_label)
        
        # Filename
        filename_item = QTableWidgetItem(image_path.name)
        filename_item.setFlags(filename_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, filename_item)
        
        # Predictions with radio buttons
        predictions_widget = self._create_predictions_widget(image_path, location_list)
        self.table.setCellWidget(row, 2, predictions_widget)
        
        # Set row height
        self.table.setRowHeight(row, 100)
    
    def _create_predictions_widget(
        self, 
        image_path: Path, 
        location_list: List[Tuple[float, float, float]]
    ) -> QWidget:
        """Create widget with radio buttons for location predictions
        
        Args:
            image_path: Path to the image
            location_list: List of (lat, lon, confidence) tuples
            
        Returns:
            QWidget containing radio buttons
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        button_group = QButtonGroup(widget)
        
        for idx, (lat, lon, confidence) in enumerate(location_list[:5]):  # Show top 5
            # Create radio button with placeholder text
            radio = QRadioButton(f"Loading... ({confidence:.1%})")
            radio.setProperty("image_path", str(image_path))
            radio.setProperty("lat", lat)
            radio.setProperty("lon", lon)
            radio.toggled.connect(self._on_location_selected)
            
            button_group.addButton(radio)
            layout.addWidget(radio)
            
            # Select first option by default
            if idx == 0:
                radio.setChecked(True)
                self.selected_locations[image_path] = (lat, lon)
        
        # Add "Skip" option
        skip_radio = QRadioButton("Skip this image")
        skip_radio.setProperty("image_path", str(image_path))
        skip_radio.setProperty("skip", True)
        skip_radio.toggled.connect(self._on_location_selected)
        button_group.addButton(skip_radio)
        layout.addWidget(skip_radio)
        
        layout.addStretch()
        
        return widget
    
    def _load_thumbnail(self, image_path: Path, width: int, height: int) -> QPixmap:
        """Load and resize image as thumbnail
        
        Args:
            image_path: Path to the image
            width: Thumbnail width
            height: Thumbnail height
            
        Returns:
            QPixmap with the thumbnail
        """
        image = Image.open(image_path)
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.read())
        
        return pixmap
    
    def _on_location_selected(self, checked):
        """Handle location selection"""
        if not checked:
            return
        
        radio = self.sender()
        image_path = Path(radio.property("image_path"))
        
        if radio.property("skip"):
            # Remove from selected locations
            self.selected_locations.pop(image_path, None)
        else:
            lat = radio.property("lat")
            lon = radio.property("lon")
            self.selected_locations[image_path] = (lat, lon)
    
    def _reverse_geocode_predictions(self):
        """Perform reverse geocoding for all predictions"""
        # Collect unique locations
        unique_locations = set()
        for location_list in self.predictions.values():
            for lat, lon, _ in location_list:
                unique_locations.add((lat, lon))
        
        # Reverse geocode each location
        for lat, lon in unique_locations:
            try:
                result = self.reverse_geocoding.reverse_geocode(lat, lon)
                if result and result.country:
                    # Create location name
                    if result.city:
                        name = f"{result.city}, {result.country}"
                    else:
                        name = result.country
                    self.location_names[(lat, lon)] = name
                    # Store full geocoding info including country_code
                    self.location_info[(lat, lon)] = {
                        'country': result.country,
                        'country_code': result.country_code,  # 3-letter ISO code
                        'city': result.city
                    }
                else:
                    self.location_names[(lat, lon)] = f"{lat:.4f}, {lon:.4f}"
                    self.location_info[(lat, lon)] = {'country': None, 'country_code': None, 'city': None}
            except Exception as e:
                print(f"Error reverse geocoding ({lat}, {lon}): {e}")
                self.location_names[(lat, lon)] = f"{lat:.4f}, {lon:.4f}"
                self.location_info[(lat, lon)] = {'country': None, 'city': None}
        
        # Update radio button labels
        self._update_location_labels()
    
    def _update_location_labels(self):
        """Update radio button labels with location names"""
        for row in range(self.table.rowCount()):
            predictions_widget = self.table.cellWidget(row, 2)
            if predictions_widget:
                layout = predictions_widget.layout()
                
                # Get image path from first radio button
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget():
                        radio = item.widget()
                        if isinstance(radio, QRadioButton) and not radio.property("skip"):
                            lat = radio.property("lat")
                            lon = radio.property("lon")
                            
                            # Get location name
                            location_name = self.location_names.get(
                                (lat, lon), 
                                f"{lat:.4f}, {lon:.4f}"
                            )
                            
                            # Extract confidence from current text
                            current_text = radio.text()
                            if "(" in current_text and ")" in current_text:
                                confidence_part = current_text[current_text.rfind("("):]
                                radio.setText(f"{location_name} {confidence_part}")
                            else:
                                radio.setText(location_name)
    
    def _apply_selected(self):
        """Apply selected locations to images"""
        if not self.selected_locations:
            QMessageBox.information(
                self,
                "No Selections",
                "No locations have been selected. Please select at least one location or close the dialog."
            )
            return
        
        count = len(self.selected_locations)
        reply = QMessageBox.question(
            self,
            "Confirm Application",
            f"Apply GPS coordinates to {count} image(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Prepare location data with coordinates and geocoding info
            locations_data = {}
            for path, (lat, lon) in self.selected_locations.items():
                loc_info = self.location_info.get((lat, lon), {'country': None, 'country_code': None, 'city': None})
                locations_data[str(path)] = {
                    'lat': lat,
                    'lon': lon,
                    'country': loc_info['country'],
                    'country_code': loc_info['country_code'],  # Include 3-letter ISO code
                    'city': loc_info['city']
                }
            # Emit signal with selected locations and their info
            self.locations_applied.emit(locations_data)
            self.accept()

