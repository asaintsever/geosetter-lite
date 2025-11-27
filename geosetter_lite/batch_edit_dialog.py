"""
Batch Metadata Edit Dialog - Edit metadata for multiple images
"""
from typing import Dict, Any, Optional
from datetime import datetime
import zoneinfo
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox, QWidget,
    QStyledItemDelegate
)
from PySide6.QtCore import Qt, QEvent, QModelIndex
from PySide6.QtGui import QKeyEvent
from .table_delegates import CountryDelegate, TZOffsetDelegate


class SimpleTZOffsetDelegate(QStyledItemDelegate):
    """Simplified TZ Offset delegate for batch edit (doesn't require image context)"""
    
    # Reuse the same timezone list
    TIMEZONE_LIST = TZOffsetDelegate.TIMEZONE_LIST
    
    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QComboBox:
        """Create a QComboBox editor with timezone options"""
        editor = QComboBox(parent)
        editor.setEditable(False)
        
        # Add timezone options (display with zone ID, city names and offsets)
        for tz_id, tz_display in self.TIMEZONE_LIST:
            # Format: "America/New_York - UTC-05:00/-04:00 - New York, Washington D.C., USA (EST/EDT)"
            display_with_zone = f"{tz_id} - {tz_display}"
            editor.addItem(display_with_zone, tz_id)
        
        return editor
    
    def setEditorData(self, editor: QComboBox, index: QModelIndex):
        """Set the current value in the editor"""
        current_offset = index.data(Qt.ItemDataRole.EditRole)
        
        # Try to find a matching timezone for the current offset
        if current_offset:
            for i, (tz_id, tz_display) in enumerate(self.TIMEZONE_LIST):
                if current_offset in tz_display:
                    editor.setCurrentIndex(i)
                    return
        
        # Default to UTC if no match
        editor.setCurrentIndex(0)
    
    def setModelData(self, editor: QComboBox, model, index: QModelIndex):
        """Save the selected timezone offset back to the model"""
        timezone_id = editor.currentData()
        
        if not timezone_id:
            return
        
        # Calculate offset from timezone ID using current date
        reference_date = datetime.now()
        offset_str = self._calculate_offset(timezone_id, reference_date)
        
        if offset_str:
            # Update the cell with the offset string
            model.setData(index, offset_str, Qt.ItemDataRole.EditRole)
    
    def _calculate_offset(self, timezone_id: str, reference_date: datetime) -> str:
        """Calculate timezone offset for a given date"""
        try:
            tz = zoneinfo.ZoneInfo(timezone_id)
            dt_with_tz = reference_date.replace(tzinfo=tz)
            offset = dt_with_tz.utcoffset()
            
            if offset:
                total_seconds = int(offset.total_seconds())
                hours = total_seconds // 3600
                minutes = abs(total_seconds % 3600) // 60
                sign = '+' if hours >= 0 else '-'
                return f"{sign}{abs(hours):02d}:{minutes:02d}"
        except Exception:
            pass
        
        return "+00:00"


class BatchEditDialog(QDialog):
    """Dialog for batch editing metadata of multiple images"""
    
    def __init__(self, num_images: int, parent=None):
        """
        Initialize the batch edit dialog
        
        Args:
            num_images: Number of images to be edited
            parent: Parent widget
        """
        super().__init__(parent)
        self.num_images = num_images
        
        self.setWindowTitle("Batch Metadata Edit")
        self.setMinimumSize(600, 400)
        self.setModal(True)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Header label
        header_text = f"Edit metadata for {self.num_images} selected images"
        header_label = QLabel(header_text)
        header_label.setStyleSheet("font-weight: bold; font-size: 12pt; padding: 10px;")
        layout.addWidget(header_label)
        
        # Info label
        info_label = QLabel(
            "Enter values for the metadata fields you want to update. "
            "Leave fields blank to keep existing values unchanged."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 5px 10px;")
        layout.addWidget(info_label)
        
        # Metadata table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Field", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        # Install event filter for Delete key
        self.table.installEventFilter(self)
        
        # Define editable fields
        self.fields = [
            ("TZ Offset", "tz_offset", "Timezone offset (e.g., +05:00, -04:30)"),
            ("Country", "country", "Country (3-letter ISO code)"),
            ("City", "city", "City name"),
            ("Headline", "headline", "Image headline/title")
        ]
        
        self.table.setRowCount(len(self.fields))
        
        for row, (label, field_key, tooltip) in enumerate(self.fields):
            # Field name (read-only)
            field_item = QTableWidgetItem(label)
            field_item.setFlags(field_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            field_item.setToolTip(tooltip)
            self.table.setItem(row, 0, field_item)
            
            # Value (editable)
            value_item = QTableWidgetItem("")
            value_item.setToolTip(tooltip)
            self.table.setItem(row, 1, value_item)
        
        # Set custom delegates for special fields
        # TZ Offset (row 0) - Use a custom simplified delegate for batch edit
        self.tz_offset_delegate = SimpleTZOffsetDelegate(self)
        self.table.setItemDelegateForRow(0, self.tz_offset_delegate)
        
        # Country (row 1)
        self.table.setItemDelegateForRow(1, CountryDelegate(self, self.table))
        
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.setDefault(True)
        self.apply_button.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(self.apply_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def eventFilter(self, obj, event):
        """Event filter to handle Delete/Backspace keys in table"""
        if obj == self.table and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if key_event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                # Get current item
                current_item = self.table.currentItem()
                if current_item and current_item.column() == 1:  # Value column
                    # Clear the cell
                    current_item.setText("")
                    return True  # Event handled
        
        return super().eventFilter(obj, event)
    
    def validate_and_accept(self):
        """Validate input and accept dialog"""
        # Get values
        values = self.get_values()
        
        # Validate TZ Offset format if provided
        tz_offset = values.get('tz_offset', '').strip()
        if tz_offset:
            # Check format: +HH:MM or -HH:MM
            if len(tz_offset) != 6 or tz_offset[0] not in ('+', '-') or tz_offset[3] != ':':
                QMessageBox.warning(
                    self,
                    "Invalid Format",
                    "TZ Offset must be in format +HH:MM or -HH:MM (e.g., +05:00, -04:30)"
                )
                return
            
            try:
                hours = int(tz_offset[1:3])
                minutes = int(tz_offset[4:6])
                if hours < 0 or hours > 14 or minutes < 0 or minutes > 59:
                    raise ValueError()
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Invalid Format",
                    "TZ Offset must have valid hours (00-14) and minutes (00-59)"
                )
                return
        
        # Check if at least one field has a value
        if not any(v.strip() for v in values.values()):
            QMessageBox.information(
                self,
                "No Values",
                "Please enter at least one value to update."
            )
            return
        
        self.accept()
    
    def get_values(self) -> Dict[str, str]:
        """
        Get the entered values
        
        Returns:
            Dictionary mapping field keys to entered values (empty strings for blank fields)
        """
        values = {}
        for row, (label, field_key, tooltip) in enumerate(self.fields):
            value_item = self.table.item(row, 1)
            if value_item:
                values[field_key] = value_item.text().strip()
        
        return values
