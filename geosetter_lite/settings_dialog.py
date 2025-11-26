"""Settings dialog for AI features configuration"""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
    QLineEdit, QPushButton, QGroupBox, QFormLayout, QFileDialog,
    QMessageBox
)
from PySide6.QtCore import Qt

from .config import Config


class SettingsDialog(QDialog):
    """Dialog for configuring AI settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Settings")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        # Load current settings
        self.ai_settings = Config.get_ai_settings()
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Similarity Settings Group
        similarity_group = QGroupBox("Photo Similarity")
        similarity_layout = QFormLayout()
        
        # Threshold slider
        threshold_layout = QHBoxLayout()
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(100)
        threshold_value = int(self.ai_settings['similarity_threshold'] * 100)
        self.threshold_slider.setValue(threshold_value)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(10)
        
        self.threshold_label = QLabel(f"{self.ai_settings['similarity_threshold']:.2f}")
        self.threshold_slider.valueChanged.connect(self._update_threshold_label)
        
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_label)
        
        similarity_layout.addRow("Similarity Threshold:", threshold_layout)
        
        # Help text
        help_label = QLabel(
            "Photos with similarity above this threshold will be grouped together.\n"
            "Higher values = more strict matching (fewer groups)."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: gray; font-size: 10px;")
        similarity_layout.addRow("", help_label)
        
        similarity_group.setLayout(similarity_layout)
        layout.addWidget(similarity_group)
        
        # Model Cache Settings Group
        cache_group = QGroupBox("Model Storage")
        cache_layout = QFormLayout()
        
        # Cache directory
        cache_dir_layout = QHBoxLayout()
        self.cache_dir_edit = QLineEdit(self.ai_settings['model_cache_dir'])
        self.cache_dir_edit.setReadOnly(True)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_cache_dir)
        
        cache_dir_layout.addWidget(self.cache_dir_edit)
        cache_dir_layout.addWidget(browse_button)
        
        cache_layout.addRow("Cache Directory:", cache_dir_layout)
        
        # Help text
        cache_help_label = QLabel(
            "Directory where AI models will be downloaded and cached.\n"
            "Models total approximately 450 MB."
        )
        cache_help_label.setWordWrap(True)
        cache_help_label.setStyleSheet("color: gray; font-size: 10px;")
        cache_layout.addRow("", cache_help_label)
        
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        # Current Settings Preview
        preview_group = QGroupBox("Current Settings")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel()
        self._update_preview()
        preview_layout.addWidget(self.preview_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self._reset_to_defaults)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        save_button.setDefault(True)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def _update_threshold_label(self, value):
        """Update threshold label when slider changes"""
        threshold = value / 100.0
        self.threshold_label.setText(f"{threshold:.2f}")
        self._update_preview()
    
    def _browse_cache_dir(self):
        """Open directory browser for cache directory"""
        current_dir = self.cache_dir_edit.text()
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Model Cache Directory",
            current_dir
        )
        
        if directory:
            self.cache_dir_edit.setText(directory)
            self._update_preview()
    
    def _reset_to_defaults(self):
        """Reset all settings to default values"""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all AI settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            defaults = Config.DEFAULT_CONFIG['ai_settings']
            self.threshold_slider.setValue(int(defaults['similarity_threshold'] * 100))
            self.cache_dir_edit.setText(defaults['model_cache_dir'])
            self._update_preview()
    
    def _update_preview(self):
        """Update the preview of current settings"""
        threshold = self.threshold_slider.value() / 100.0
        cache_dir = self.cache_dir_edit.text()
        
        preview_text = f"""
<b>Similarity Threshold:</b> {threshold:.2f}<br>
<b>Cache Directory:</b> {cache_dir}
        """
        self.preview_label.setText(preview_text.strip())
    
    def get_settings(self):
        """Get the current settings from the dialog"""
        return {
            'similarity_threshold': self.threshold_slider.value() / 100.0,
            'model_cache_dir': self.cache_dir_edit.text()
        }
    
    def accept(self):
        """Save settings and close dialog"""
        settings = self.get_settings()
        
        # Validate cache directory
        cache_dir = Path(settings['model_cache_dir'])
        if not cache_dir.exists():
            reply = QMessageBox.question(
                self,
                "Create Directory",
                f"The directory '{cache_dir}' does not exist.\n\nDo you want to create it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    cache_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to create directory:\n{str(e)}"
                    )
                    return
            else:
                return
        
        # Save settings
        Config.set_ai_settings(settings)
        super().accept()

