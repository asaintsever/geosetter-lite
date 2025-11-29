"""Settings dialog for AI features configuration"""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
    QLineEdit, QPushButton, QGroupBox, QFormLayout, QFileDialog,
    QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt

from ..core.config import Config


class SettingsDialog(QDialog):
    """Dialog for configuring AI settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Settings")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        # Load current settings
        self.ai_settings = Config.get_ai_settings()
        self.app_settings = Config.get_app_settings()
        
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
        
        # ExifTool Settings Group
        exiftool_group = QGroupBox("ExifTool")
        exiftool_layout = QFormLayout()
        
        # Backup files checkbox
        self.backup_checkbox = QCheckBox("Create backup files (_original)")
        self.backup_checkbox.setChecked(self.app_settings.get('exiftool_create_backups', True))
        self.backup_checkbox.stateChanged.connect(self._update_preview)
        exiftool_layout.addRow(self.backup_checkbox)
        
        # Help text
        backup_help_label = QLabel(
            "When enabled, ExifTool creates backup files with '_original' suffix.\n"
            "Disable to save disk space and avoid backup file clutter."
        )
        backup_help_label.setWordWrap(True)
        backup_help_label.setStyleSheet("color: gray; font-size: 10px;")
        exiftool_layout.addRow("", backup_help_label)
        
        exiftool_group.setLayout(exiftool_layout)
        layout.addWidget(exiftool_group)
        
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
            ai_defaults = Config.DEFAULT_CONFIG['ai_settings']
            app_defaults = Config.DEFAULT_CONFIG['app_settings']
            self.threshold_slider.setValue(int(ai_defaults['similarity_threshold'] * 100))
            self.cache_dir_edit.setText(ai_defaults['model_cache_dir'])
            self.backup_checkbox.setChecked(app_defaults.get('exiftool_create_backups', True))
            self._update_preview()
    
    def _update_preview(self):
        """Update the preview of current settings"""
        threshold = self.threshold_slider.value() / 100.0
        cache_dir = self.cache_dir_edit.text()
        backups_enabled = self.backup_checkbox.isChecked()
        
        preview_text = f"""
<b>Similarity Threshold:</b> {threshold:.2f}<br>
<b>Cache Directory:</b> {cache_dir}<br>
<b>ExifTool Backups:</b> {'Enabled' if backups_enabled else 'Disabled'}
        """
        self.preview_label.setText(preview_text.strip())
    
    def get_settings(self):
        """Get the current settings from the dialog"""
        ai_settings = {
            'similarity_threshold': self.threshold_slider.value() / 100.0,
            'model_cache_dir': self.cache_dir_edit.text()
        }
        app_settings = {
            'exiftool_create_backups': self.backup_checkbox.isChecked()
        }
        return {'ai_settings': ai_settings, 'app_settings': app_settings}
    
    def accept(self):
        """Save settings and close dialog"""
        settings = self.get_settings()
        
        # Validate cache directory
        cache_dir = Path(settings['ai_settings']['model_cache_dir'])
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
        Config.set_ai_settings(settings['ai_settings'])
        
        # Update app settings
        app_settings = Config.get_app_settings()
        app_settings['exiftool_create_backups'] = settings['app_settings']['exiftool_create_backups']
        Config.set_app_settings(app_settings)
        
        super().accept()

