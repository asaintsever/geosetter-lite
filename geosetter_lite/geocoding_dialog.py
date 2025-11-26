"""
Geocoding Dialog - Display and edit reverse geocoding results
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QGroupBox, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from typing import Optional, Tuple
from .table_delegates import CountryDelegate


class GeocodingDialog(QDialog):
    """Dialog to display and edit reverse geocoding results"""
    
    def __init__(self, country: Optional[str], city: Optional[str], 
                 num_images: int, parent=None):
        """
        Initialize the geocoding dialog
        
        Args:
            country: Country name from reverse geocoding
            city: City name from reverse geocoding
            num_images: Number of images being updated
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.country = country
        self.city = city
        self.num_images = num_images
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Reverse Geocoding Results")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Info label
        info_text = f"Reverse geocoding found the following location for {self.num_images} image(s):"
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Results group
        results_group = QGroupBox("Location Information")
        results_layout = QFormLayout()
        
        # Country field - use QComboBox with country list
        self.country_combo = QComboBox()
        self.country_combo.setEditable(True)
        self.country_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        # Populate country list from CountryDelegate
        for code, name in CountryDelegate.COUNTRY_LIST:
            self.country_combo.addItem(f"{name} ({code})", (code, name))
        
        # Enable filtering
        self.country_combo.completer().setCompletionMode(
            self.country_combo.completer().CompletionMode.PopupCompletion
        )
        self.country_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        
        # Try to set the current country if provided
        if self.country:
            for i in range(self.country_combo.count()):
                code, name = self.country_combo.itemData(i)
                if name == self.country:
                    self.country_combo.setCurrentIndex(i)
                    break
        
        results_layout.addRow("Country:", self.country_combo)
        
        # City field
        self.city_edit = QLineEdit()
        self.city_edit.setText(self.city or "")
        self.city_edit.setPlaceholderText("City name")
        results_layout.addRow("City:", self.city_edit)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Note label
        note_label = QLabel(
            "You can modify the values above before applying them to the image metadata."
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(note_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("Apply")
        apply_button.setDefault(True)
        apply_button.clicked.connect(self.accept)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_values(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Get the edited values from the dialog
        
        Returns:
            Tuple of (country_name, country_code, city)
        """
        # Get selected country data
        data = self.country_combo.currentData()
        if data:
            country_code, country_name = data
        else:
            country_name = None
            country_code = None
        
        city = self.city_edit.text().strip() or None
        
        return country_name, country_code, city

