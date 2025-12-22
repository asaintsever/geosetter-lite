"""
Map Panel - Map widget with toolbar
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QPushButton, QToolButton, QLabel, QFrame
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QPen
from .map_widget import MapWidget


class MapPanel(QWidget):
    """Panel containing map and toolbar"""
    
    # Signals
    update_coordinates_requested = Signal()  # Update selected images with active marker coords
    set_marker_from_selection_requested = Signal()  # Set active marker from selected image
    batch_edit_requested = Signal()  # Batch edit metadata for multiple selected images
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
        
        # Create icon for "Batch Edit"
        self.batch_edit_icon = self._create_batch_edit_icon()
        
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
        
        # Draw a location pin (left side) - RED
        pen = QPen(QColor(220, 50, 50), 2.5)
        painter.setPen(pen)
        painter.setBrush(QColor(255, 80, 80))
        # Pin head
        painter.drawEllipse(6, 8, 10, 10)
        # Pin point
        painter.drawLine(11, 18, 11, 26)
        painter.drawLine(9, 24, 11, 26)
        painter.drawLine(13, 24, 11, 26)
        
        # Draw thick arrow pointing right
        painter.setPen(QPen(QColor(50, 50, 50), 3))
        painter.setBrush(QColor(80, 80, 80))
        # Arrow shaft
        painter.drawLine(18, 20, 28, 20)
        # Arrow head
        painter.drawLine(24, 15, 28, 20)
        painter.drawLine(24, 25, 28, 20)
        painter.drawLine(28, 20, 24, 15)
        painter.drawLine(28, 20, 24, 25)
        
        # Draw multiple images icon (right side) - BLUE
        painter.setPen(QPen(QColor(50, 100, 200), 2.5))
        painter.setBrush(QColor(100, 150, 255, 100))
        # First image (back)
        painter.drawRect(33, 14, 10, 10)
        # Second image (front)
        painter.setBrush(QColor(100, 150, 255))
        painter.drawRect(30, 17, 10, 10)
        # Mountain in front image
        painter.setPen(QPen(QColor(50, 100, 200), 1.5))
        painter.drawLine(31, 25, 33, 22)
        painter.drawLine(33, 22, 35, 24)
        painter.drawLine(35, 24, 38, 20)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_set_marker_icon(self) -> QIcon:
        """Create icon for setting marker from image (image -> marker)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw image icon (left side) - BLUE
        painter.setPen(QPen(QColor(50, 100, 200), 2.5))
        painter.setBrush(QColor(100, 150, 255))
        painter.drawRect(5, 14, 12, 12)
        # Mountain in image
        painter.setPen(QPen(QColor(50, 100, 200), 1.5))
        painter.drawLine(7, 23, 9, 19)
        painter.drawLine(9, 19, 11, 21)
        painter.drawLine(11, 21, 14, 17)
        
        # Draw thick arrow pointing right
        painter.setPen(QPen(QColor(50, 50, 50), 3))
        painter.setBrush(QColor(80, 80, 80))
        # Arrow shaft
        painter.drawLine(19, 20, 29, 20)
        # Arrow head
        painter.drawLine(25, 15, 29, 20)
        painter.drawLine(25, 25, 29, 20)
        painter.drawLine(29, 20, 25, 15)
        painter.drawLine(29, 20, 25, 25)
        
        # Draw a location pin (right side) - RED
        pen = QPen(QColor(220, 50, 50), 2.5)
        painter.setPen(pen)
        painter.setBrush(QColor(255, 80, 80))
        # Pin head
        painter.drawEllipse(32, 8, 10, 10)
        # Pin point
        painter.drawLine(37, 18, 37, 26)
        painter.drawLine(35, 24, 37, 26)
        painter.drawLine(39, 24, 37, 26)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_batch_edit_icon(self) -> QIcon:
        """Create icon for batch editing metadata"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw multiple documents/images stacked
        painter.setPen(QPen(QColor(50, 100, 200), 2.5))
        painter.setBrush(QColor(100, 150, 255, 80))
        
        # Back document
        painter.drawRect(18, 12, 16, 20)
        
        # Middle document
        painter.setBrush(QColor(100, 150, 255, 120))
        painter.drawRect(15, 14, 16, 20)
        
        # Front document
        painter.setBrush(QColor(100, 150, 255))
        painter.drawRect(12, 16, 16, 20)
        
        # Draw pencil/edit icon
        painter.setPen(QPen(QColor(200, 120, 50), 2.5))
        painter.setBrush(QColor(240, 160, 80))
        
        # Pencil body
        painter.drawLine(30, 22, 38, 30)
        painter.drawLine(28, 24, 36, 32)
        
        # Pencil tip
        painter.setPen(QPen(QColor(100, 50, 20), 2))
        painter.drawLine(30, 22, 28, 24)
        
        # Pencil eraser
        painter.setPen(QPen(QColor(220, 80, 80), 2))
        painter.drawPoint(38, 30)
        painter.drawPoint(36, 32)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_repair_icon(self) -> QIcon:
        """Create icon for repairing metadata (medical cross/first aid icon)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circular background - RED/PINK
        painter.setPen(QPen(QColor(200, 50, 50), 2))
        painter.setBrush(QColor(220, 60, 60))  # Red background
        painter.drawEllipse(10, 10, 28, 28)
        
        # Draw white medical cross
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255))  # White cross
        
        # Vertical bar of cross
        painter.drawRect(22, 14, 4, 20)
        
        # Horizontal bar of cross
        painter.drawRect(16, 22, 16, 4)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_set_taken_date_icon(self) -> QIcon:
        """Create icon for setting Taken Date from file creation date (file -> calendar)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw file icon (left side) - GREY
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QColor(180, 180, 180))
        # File shape
        painter.drawRect(6, 14, 10, 14)
        # File corner fold
        painter.drawLine(16, 14, 16, 18)
        painter.drawLine(16, 18, 12, 18)
        
        # Draw thick arrow pointing right
        painter.setPen(QPen(QColor(50, 50, 50), 3))
        painter.setBrush(QColor(80, 80, 80))
        # Arrow shaft
        painter.drawLine(18, 21, 26, 21)
        # Arrow head
        painter.drawLine(23, 17, 26, 21)
        painter.drawLine(23, 25, 26, 21)
        
        # Draw calendar icon (right side) - BLUE
        painter.setPen(QPen(QColor(50, 100, 200), 2))
        painter.setBrush(QColor(100, 150, 255))
        # Calendar body
        painter.drawRect(28, 16, 12, 12)
        # Calendar header
        painter.setBrush(QColor(50, 100, 200))
        painter.drawRect(28, 16, 12, 3)
        # Calendar rings
        painter.drawLine(30, 15, 30, 17)
        painter.drawLine(38, 15, 38, 17)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_set_gps_date_icon(self) -> QIcon:
        """Create icon for setting GPS Date from Taken Date (calendar -> GPS)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw calendar icon (left side) - BLUE
        painter.setPen(QPen(QColor(50, 100, 200), 2))
        painter.setBrush(QColor(100, 150, 255))
        # Calendar body
        painter.drawRect(6, 16, 12, 12)
        # Calendar header
        painter.setBrush(QColor(50, 100, 200))
        painter.drawRect(6, 16, 12, 3)
        # Calendar rings
        painter.drawLine(8, 15, 8, 17)
        painter.drawLine(16, 15, 16, 17)
        
        # Draw thick arrow pointing right
        painter.setPen(QPen(QColor(50, 50, 50), 3))
        painter.setBrush(QColor(80, 80, 80))
        # Arrow shaft
        painter.drawLine(20, 22, 28, 22)
        # Arrow head
        painter.drawLine(25, 18, 28, 22)
        painter.drawLine(25, 26, 28, 22)
        
        # Draw GPS pin (right side) - GREEN
        painter.setPen(QPen(QColor(50, 150, 50), 2))
        painter.setBrush(QColor(80, 200, 80))
        # Pin head
        painter.drawEllipse(32, 14, 8, 8)
        # Pin point
        painter.drawLine(36, 22, 36, 28)
        painter.drawLine(34, 26, 36, 28)
        painter.drawLine(38, 26, 36, 28)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_reverse_geocoding_icon(self) -> QIcon:
        """Create icon for reverse geocoding (globe/map with magnifying glass)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw globe/earth (left/center) - BLUE/GREEN
        painter.setPen(QPen(QColor(50, 100, 200), 2.5))
        painter.setBrush(QColor(100, 150, 255, 180))
        # Globe circle
        painter.drawEllipse(8, 10, 20, 20)
        
        # Draw continents/land masses on globe - GREEN
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(80, 180, 80))
        # Simplified continent shapes
        painter.drawEllipse(11, 14, 6, 5)  # Top left landmass
        painter.drawEllipse(18, 13, 7, 6)  # Top right landmass
        painter.drawEllipse(13, 21, 8, 5)  # Bottom landmass
        
        # Draw magnifying glass (right side) - ORANGE/GOLD
        painter.setPen(QPen(QColor(200, 120, 20), 2.5))
        painter.setBrush(QColor(255, 200, 100, 100))
        # Magnifying glass lens
        painter.drawEllipse(26, 18, 12, 12)
        # Handle
        painter.setPen(QPen(QColor(150, 90, 20), 3))
        painter.drawLine(35, 27, 40, 32)
        
        # Draw small location pin inside magnifying glass - RED
        painter.setPen(QPen(QColor(220, 50, 50), 1.5))
        painter.setBrush(QColor(255, 80, 80))
        # Pin head (small)
        painter.drawEllipse(30, 22, 4, 4)
        # Pin point (small)
        painter.drawLine(32, 26, 32, 28)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_reverse_geocoding_icon_checked(self) -> QIcon:
        """Create icon for reverse geocoding when checked (brighter/enabled state)"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw globe/earth (left/center) - BRIGHT BLUE/GREEN (more vibrant when checked)
        painter.setPen(QPen(QColor(30, 120, 255), 3))
        painter.setBrush(QColor(80, 180, 255, 220))
        # Globe circle
        painter.drawEllipse(8, 10, 20, 20)
        
        # Draw continents/land masses on globe - BRIGHT GREEN
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(50, 220, 50))
        # Simplified continent shapes
        painter.drawEllipse(11, 14, 6, 5)  # Top left landmass
        painter.drawEllipse(18, 13, 7, 6)  # Top right landmass
        painter.drawEllipse(13, 21, 8, 5)  # Bottom landmass
        
        # Draw magnifying glass (right side) - BRIGHT ORANGE/GOLD
        painter.setPen(QPen(QColor(255, 150, 0), 3))
        painter.setBrush(QColor(255, 220, 100, 150))
        # Magnifying glass lens
        painter.drawEllipse(26, 18, 12, 12)
        # Handle
        painter.setPen(QPen(QColor(200, 120, 0), 3.5))
        painter.drawLine(35, 27, 40, 32)
        
        # Draw small location pin inside magnifying glass - BRIGHT RED
        painter.setPen(QPen(QColor(255, 30, 30), 2))
        painter.setBrush(QColor(255, 60, 60))
        # Pin head (small)
        painter.drawEllipse(30, 22, 4, 4)
        # Pin point (small)
        painter.drawLine(32, 26, 32, 28)
        
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
        
        # Action: Update selected images with active marker coordinates
        self.update_coords_action = QAction(self.update_gps_icon, "Update GPS", self)
        self.update_coords_action.setToolTip("Update selected images with active marker coordinates")
        self.update_coords_action.setEnabled(False)
        self.update_coords_action.triggered.connect(self.update_coordinates_requested.emit)
        toolbar.addAction(self.update_coords_action)
        
        toolbar.addSeparator()
        
        # Action: Set active marker from selected image
        self.set_marker_action = QAction(self.set_marker_icon, "Set Marker", self)
        self.set_marker_action.setToolTip("Set active marker from selected image GPS coordinates")
        self.set_marker_action.setEnabled(False)
        self.set_marker_action.triggered.connect(self.set_marker_from_selection_requested.emit)
        toolbar.addAction(self.set_marker_action)
        
        toolbar.addSeparator()
        
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
        
        toolbar.addSeparator()
        
        # Action: Set GPS Date from Taken Date
        self.set_gps_date_action = QAction(self.set_gps_date_icon, "Set GPS Date", self)
        self.set_gps_date_action.setToolTip("Set GPS Date from Taken Date for selected images")
        self.set_gps_date_action.setEnabled(False)
        self.set_gps_date_action.triggered.connect(self.set_gps_date_from_taken_requested.emit)
        toolbar.addAction(self.set_gps_date_action)
        
        toolbar.addSeparator()
        
        # Action: Batch edit metadata for multiple selected images
        self.batch_edit_action = QAction(self.batch_edit_icon, "Batch Edit", self)
        self.batch_edit_action.setToolTip("Edit metadata for multiple selected images")
        self.batch_edit_action.setEnabled(False)
        self.batch_edit_action.triggered.connect(self.batch_edit_requested.emit)
        toolbar.addAction(self.batch_edit_action)
        
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
    
    def enable_batch_edit_action(self, enabled: bool):
        """
        Enable or disable the batch edit action
        
        Args:
            enabled: True to enable, False to disable
        """
        self.batch_edit_action.setEnabled(enabled)
    
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

