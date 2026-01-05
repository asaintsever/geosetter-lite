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
        similarity_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        similarity_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
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
        help_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        similarity_layout.addRow(help_label)
        
        similarity_group.setLayout(similarity_layout)
        layout.addWidget(similarity_group)
        
        # Model Cache Settings Group
        cache_group = QGroupBox("Model Storage")
        cache_layout = QFormLayout()
        cache_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        cache_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
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
            "Directory where AI models will be downloaded and cached."
        )
        cache_help_label.setWordWrap(True)
        cache_help_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        cache_layout.addRow(cache_help_label)
        
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        # ExifTool Settings Group
        exiftool_group = QGroupBox("ExifTool")
        exiftool_layout = QFormLayout()
        exiftool_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        exiftool_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Backup files checkbox
        self.backup_checkbox = QCheckBox("Create backup files (_original)")
        self.backup_checkbox.setChecked(self.app_settings.get('exiftool_create_backups', True))
        exiftool_layout.addRow(self.backup_checkbox)
        
        # Help text
        backup_help_label = QLabel(
            "When enabled, ExifTool creates backup files with '_original' suffix.\n"
            "Disable to save disk space and avoid backup file clutter."
        )
        backup_help_label.setWordWrap(True)
        backup_help_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        exiftool_layout.addRow(backup_help_label)
        
        exiftool_group.setLayout(exiftool_layout)
        layout.addWidget(exiftool_group)
        
        # Map Settings Group
        map_group = QGroupBox("Map")
        map_layout = QFormLayout()
        map_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        map_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Preserve zoom level checkbox
        self.preserve_zoom_checkbox = QCheckBox("Preserve current zoom level when selecting photos")
        self.preserve_zoom_checkbox.setChecked(self.app_settings.get('preserve_map_zoom', False))
        self.preserve_zoom_checkbox.stateChanged.connect(self._on_preserve_zoom_changed)
        map_layout.addRow(self.preserve_zoom_checkbox)
        
        # Default zoom level
        zoom_layout = QHBoxLayout()
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(1)
        self.zoom_slider.setMaximum(19)
        self.zoom_slider.setValue(self.app_settings.get('default_map_zoom', 10))
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_slider.setTickInterval(2)
        
        self.zoom_label = QLabel(str(self.app_settings.get('default_map_zoom', 10)))
        self.zoom_slider.valueChanged.connect(self._update_zoom_label)
        
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_label)
        
        map_layout.addRow("Default Zoom Level:", zoom_layout)
        
        # Help text
        zoom_help_label = QLabel(
            "Default zoom level when selecting a single photo with GPS coordinates.\n"
            "Lower values = wider area view, Higher values = closer detail view.\n"
            "Typical: 10 (~10km scale), 13 (~2km), 15 (~300m)\n"
            "Disabled when 'Preserve current zoom level' is enabled."
        )
        zoom_help_label.setWordWrap(True)
        zoom_help_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        self.zoom_help_label = zoom_help_label  # Store reference for later updates
        map_layout.addRow(zoom_help_label)
        
        # Initialize zoom slider state based on preserve checkbox
        self._on_preserve_zoom_changed()
        
        map_group.setLayout(map_layout)
        layout.addWidget(map_group)
        
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
    
    def _update_zoom_label(self, value):
        """Update zoom label when slider changes"""
        self.zoom_label.setText(str(value))
    
    def _on_preserve_zoom_changed(self):
        """Handle preserve zoom checkbox state change"""
        preserve = self.preserve_zoom_checkbox.isChecked()
        # Disable zoom slider and label when preserve is enabled
        self.zoom_slider.setEnabled(not preserve)
        self.zoom_label.setEnabled(not preserve)
    
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
            self.preserve_zoom_checkbox.setChecked(app_defaults.get('preserve_map_zoom', False))
            self.zoom_slider.setValue(app_defaults.get('default_map_zoom', 10))
            self._on_preserve_zoom_changed()
    
    def get_settings(self):
        """Get the current settings from the dialog"""
        ai_settings = {
            'similarity_threshold': self.threshold_slider.value() / 100.0,
            'model_cache_dir': self.cache_dir_edit.text()
        }
        app_settings = {
            'exiftool_create_backups': self.backup_checkbox.isChecked(),
            'preserve_map_zoom': self.preserve_zoom_checkbox.isChecked(),
            'default_map_zoom': self.zoom_slider.value()
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
        app_settings['preserve_map_zoom'] = settings['app_settings']['preserve_map_zoom']
        app_settings['default_map_zoom'] = settings['app_settings']['default_map_zoom']
        Config.set_app_settings(app_settings)
        
        super().accept()

