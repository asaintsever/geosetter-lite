"""
Map Panel - Map widget with toolbar
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QPushButton, QToolButton, QLabel, QFrame
from PySide6.QtCore import Signal, Qt, QSize, QPointF
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QPen
from .map_widget import MapWidget


class MapPanel(QWidget):
    """Panel containing map and toolbar"""
    
    # Signals
    update_coordinates_requested = Signal()  # Update selected images with active marker coords
    set_marker_from_selection_requested = Signal()  # Set active marker from selected image
    repair_metadata_requested = Signal()  # Repair metadata for selected images
    set_taken_date_from_creation_requested = Signal()  # Set Taken Date from file creation date
    set_gps_date_from_taken_requested = Signal()  # Set GPS Date from Taken Date
    
    def __init__(self, parent=None):
        """Initialize the map panel"""
        super().__init__(parent)
        
        self._create_icons()
        self.init_ui()
    
    def _create_icons(self):
        """Create icons for toolbar buttons"""
        # Create icon for "Update GPS" (marker to images)
        self.update_gps_icon = self._create_update_gps_icon()
        
        # Create icon for "Set Marker" (image to marker)
        self.set_marker_icon = self._create_set_marker_icon()
        
        # Create icon for "Repair Metadata"
        self.repair_icon = self._create_repair_icon()
        
        # Create icon for "Set Taken Date from File"
        self.set_taken_date_icon = self._create_set_taken_date_icon()
        
        # Create icon for "Set GPS Date from Taken Date"
        self.set_gps_date_icon = self._create_set_gps_date_icon()
        
        # Create icon for "Reverse Geocoding"
        self.reverse_geocoding_icon = self._create_reverse_geocoding_icon()
        self.reverse_geocoding_icon_checked = self._create_reverse_geocoding_icon_checked()
    
    def _create_update_gps_icon(self) -> QIcon:
        """Create icon for updating GPS coordinates (marker -> images)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Simple blue location pin
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(33, 150, 243))  # Blue
        
        # Pin circle (larger, simpler)
        painter.drawEllipse(12, 6, 24, 24)
        
        # Pin point (simple triangle)
        points = [(24, 30), (18, 42), (30, 42)]
        painter.drawPolygon([QPointF(x, y) for x, y in points])
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_set_marker_icon(self) -> QIcon:
        """Create icon for setting marker from image (image -> marker)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Simple green camera
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(76, 175, 80))  # Green
        
        # Camera body (rounded rectangle)
        painter.drawRoundedRect(8, 16, 32, 22, 4, 4)
        
        # Lens (large circle)
        painter.setBrush(QColor(46, 125, 50))  # Darker green
        painter.drawEllipse(16, 20, 16, 16)
        
        # Small viewfinder on top
        painter.setBrush(QColor(76, 175, 80))
        painter.drawRoundedRect(18, 12, 12, 6, 2, 2)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_repair_icon(self) -> QIcon:
        """Create icon for repairing metadata (first aid kit)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Red first aid kit box
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(244, 67, 54))  # Red
        
        # Main kit body (rectangle)
        painter.drawRoundedRect(10, 14, 28, 22, 3, 3)
        
        # Handle on top
        painter.setBrush(QColor(211, 47, 47))  # Darker red
        painter.drawRoundedRect(17, 10, 14, 6, 2, 2)
        
        # White medical cross
        painter.setBrush(QColor(255, 255, 255))
        # Vertical bar
        painter.drawRoundedRect(22, 19, 4, 12, 1, 1)
        # Horizontal bar
        painter.drawRoundedRect(18, 23, 12, 4, 1, 1)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_set_taken_date_icon(self) -> QIcon:
        """Create icon for setting Taken Date from file creation date (calendar with plus)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Simple purple calendar
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(156, 39, 176))  # Purple
        
        # Calendar body
        painter.drawRoundedRect(10, 12, 28, 28, 4, 4)
        
        # Calendar header (darker)
        painter.setBrush(QColor(106, 27, 154))
        painter.drawRoundedRect(10, 12, 28, 10, 4, 4)
        painter.drawRect(10, 18, 28, 4)
        
        # Calendar rings
        painter.setBrush(QColor(186, 104, 200))
        painter.drawRoundedRect(16, 10, 4, 8, 2, 2)
        painter.drawRoundedRect(28, 10, 4, 8, 2, 2)
        
        # Large green plus badge
        painter.setBrush(QColor(76, 175, 80))
        painter.drawEllipse(26, 28, 14, 14)
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(33, 32, 33, 38)  # Vertical
        painter.drawLine(30, 35, 36, 35)  # Horizontal
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_set_gps_date_icon(self) -> QIcon:
        """Create icon for setting GPS Date from Taken Date (calendar with GPS badge)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Simple teal calendar
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 150, 136))  # Teal
        
        # Calendar body
        painter.drawRoundedRect(10, 12, 28, 28, 4, 4)
        
        # Calendar header (darker)
        painter.setBrush(QColor(0, 121, 107))
        painter.drawRoundedRect(10, 12, 28, 10, 4, 4)
        painter.drawRect(10, 18, 28, 4)
        
        # Calendar rings
        painter.setBrush(QColor(77, 182, 172))
        painter.drawRoundedRect(16, 10, 4, 8, 2, 2)
        painter.drawRoundedRect(28, 10, 4, 8, 2, 2)
        
        # Blue pin badge (bottom right)
        painter.setBrush(QColor(33, 150, 243))  # Blue
        # Pin circle
        painter.drawEllipse(27, 28, 12, 12)
        # Pin point
        points = [(33, 40), (29, 44), (37, 44)]
        painter.drawPolygon([QPointF(x, y) for x, y in points])
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_reverse_geocoding_icon(self) -> QIcon:
        """Create icon for reverse geocoding (globe with magnifying glass)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Simple blue globe
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(66, 165, 245))  # Light blue
        painter.drawEllipse(6, 8, 26, 26)
        
        # Simple latitude lines (white)
        painter.setPen(QPen(QColor(255, 255, 255, 120), 2))
        painter.drawLine(8, 15, 30, 15)
        painter.drawLine(8, 21, 30, 21)
        painter.drawLine(8, 27, 30, 27)
        
        # Orange magnifying glass
        painter.setPen(QPen(QColor(255, 152, 0), 4))  # Orange
        painter.setBrush(QColor(255, 255, 255, 60))
        painter.drawEllipse(22, 18, 18, 18)  # Lens
        
        # Handle
        painter.setPen(QPen(QColor(255, 152, 0), 5))
        painter.drawLine(36, 32, 42, 38)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_reverse_geocoding_icon_checked(self) -> QIcon:
        """Create icon for reverse geocoding when checked (brighter/enabled state)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Brighter blue globe when checked
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(100, 181, 246))  # Brighter blue
        painter.drawEllipse(6, 8, 26, 26)
        
        # Brighter latitude lines
        painter.setPen(QPen(QColor(255, 255, 255, 180), 2.5))
        painter.drawLine(8, 15, 30, 15)
        painter.drawLine(8, 21, 30, 21)
        painter.drawLine(8, 27, 30, 27)
        
        # Brighter orange magnifying glass
        painter.setPen(QPen(QColor(255, 183, 77), 5))  # Lighter orange
        painter.setBrush(QColor(255, 255, 255, 100))
        painter.drawEllipse(22, 18, 18, 18)  # Lens
        
        # Brighter handle
        painter.setPen(QPen(QColor(255, 183, 77), 6))
        painter.drawLine(36, 32, 42, 38)
        
        painter.end()
        return QIcon(pixmap)
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(32, 32))
        
        # Add hover effect styling to toolbar buttons
        toolbar.setStyleSheet("""
            QToolBar QToolButton {
                border: none;
                padding: 4px;
                border-radius: 4px;
            }
            QToolBar QToolButton:hover {
                background-color: rgba(100, 150, 200, 0.3);
            }
            QToolBar QToolButton:pressed {
                background-color: rgba(100, 150, 200, 0.5);
            }
            QToolBar QToolButton:checked {
                background-color: rgba(100, 150, 200, 0.4);
            }
            QToolBar QToolButton:checked:hover {
                background-color: rgba(100, 150, 200, 0.5);
            }
        """)
        
        # Action: Update selected images with active marker coordinates
        self.update_coords_action = QAction(self.update_gps_icon, "Update GPS", self)
        self.update_coords_action.setToolTip("Update selected images with active marker coordinates")
        self.update_coords_action.setEnabled(False)
        self.update_coords_action.triggered.connect(self.update_coordinates_requested.emit)
        toolbar.addAction(self.update_coords_action)
        
        # Action: Set active marker from selected image
        self.set_marker_action = QAction(self.set_marker_icon, "Set Marker", self)
        self.set_marker_action.setToolTip("Set active marker from selected image GPS coordinates")
        self.set_marker_action.setEnabled(False)
        self.set_marker_action.triggered.connect(self.set_marker_from_selection_requested.emit)
        toolbar.addAction(self.set_marker_action)
        
        # Reverse geocoding toggle action (third position)
        self.reverse_geocoding_action = QAction(self.reverse_geocoding_icon, "Auto Reverse Geocoding", self)
        self.reverse_geocoding_action.setToolTip("Automatically determine country and city from GPS coordinates")
        self.reverse_geocoding_action.setCheckable(True)
        self.reverse_geocoding_action.setChecked(False)
        self.reverse_geocoding_action.toggled.connect(self._on_reverse_geocoding_toggled)
        toolbar.addAction(self.reverse_geocoding_action)
        
        toolbar.addSeparator()
        
        # Action: Set Taken Date from file creation date
        self.set_taken_date_action = QAction(self.set_taken_date_icon, "Set Taken Date", self)
        self.set_taken_date_action.setToolTip("Set Taken Date from file creation date for selected images")
        self.set_taken_date_action.setEnabled(False)
        self.set_taken_date_action.triggered.connect(self.set_taken_date_from_creation_requested.emit)
        toolbar.addAction(self.set_taken_date_action)
        
        # Action: Set GPS Date from Taken Date
        self.set_gps_date_action = QAction(self.set_gps_date_icon, "Set GPS Date", self)
        self.set_gps_date_action.setToolTip("Set GPS Date from Taken Date for selected images")
        self.set_gps_date_action.setEnabled(False)
        self.set_gps_date_action.triggered.connect(self.set_gps_date_from_taken_requested.emit)
        toolbar.addAction(self.set_gps_date_action)
        
        toolbar.addSeparator()
        
        # Action: Repair metadata for selected images (last action)
        self.repair_action = QAction(self.repair_icon, "Repair Metadata", self)
        self.repair_action.setToolTip("Repair/fix metadata for selected images")
        self.repair_action.setEnabled(False)
        self.repair_action.triggered.connect(self.repair_metadata_requested.emit)
        toolbar.addAction(self.repair_action)
        
        layout.addWidget(toolbar)
        
        # Create map widget
        self.map_widget = MapWidget()
        self.map_widget.map_clicked.connect(self._on_map_clicked)
        layout.addWidget(self.map_widget)
        
        # Create status bar below map for coordinates
        status_bar = QFrame()
        status_bar.setFrameShape(QFrame.Shape.StyledPanel)
        status_bar.setFrameShadow(QFrame.Shadow.Sunken)
        status_bar.setMaximumHeight(30)
        
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        self.info_label = QLabel("Click map to set active marker")
        self.info_label.setStyleSheet("color: #555; font-size: 11pt;")
        status_layout.addWidget(self.info_label)
        
        status_bar.setLayout(status_layout)
        layout.addWidget(status_bar)
        
        self.setLayout(layout)
    
    def _on_map_clicked(self, lat: float, lng: float):
        """Handle map click - enable update button only if images are selected"""
        self.info_label.setText(f"Active: {lat:.6f}°, {lng:.6f}°")
        # Note: The main window will check if images are selected and enable/disable accordingly
        # We signal that an active marker exists, but main window controls final state
    
    def enable_set_marker_action(self, enabled: bool):
        """
        Enable or disable the set marker action
        
        Args:
            enabled: True to enable, False to disable
        """
        self.set_marker_action.setEnabled(enabled)
    
    def enable_update_coords_action(self, enabled: bool):
        """
        Enable or disable the update coordinates action
        
        Args:
            enabled: True to enable, False to disable
        """
        self.update_coords_action.setEnabled(enabled)
    
    def enable_repair_action(self, enabled: bool):
        """
        Enable or disable the repair metadata action
        
        Args:
            enabled: True to enable, False to disable
        """
        self.repair_action.setEnabled(enabled)
    
    def enable_set_taken_date_action(self, enabled: bool):
        """
        Enable or disable the set taken date action
        
        Args:
            enabled: True to enable, False to disable
        """
        self.set_taken_date_action.setEnabled(enabled)
    
    def enable_set_gps_date_action(self, enabled: bool):
        """
        Enable or disable the set GPS date action
        
        Args:
            enabled: True to enable, False to disable
        """
        self.set_gps_date_action.setEnabled(enabled)
    
    def is_reverse_geocoding_enabled(self) -> bool:
        """
        Check if reverse geocoding is enabled
        
        Returns:
            True if reverse geocoding action is checked, False otherwise
        """
        return self.reverse_geocoding_action.isChecked()
    
    def _on_reverse_geocoding_toggled(self, checked: bool):
        """
        Handle reverse geocoding toggle state change
        
        Args:
            checked: True if checked/enabled, False if unchecked/disabled
        """
        # Update icon based on checked state
        if checked:
            self.reverse_geocoding_action.setIcon(self.reverse_geocoding_icon_checked)
        else:
            self.reverse_geocoding_action.setIcon(self.reverse_geocoding_icon)

