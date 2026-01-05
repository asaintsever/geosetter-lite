"""
Rename Dialog - Rename files based on metadata patterns
"""
import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ..models.image_model import ImageModel
from ..core.config import Config


class RenameDialog(QDialog):
    """Dialog for renaming files based on metadata patterns"""
    
    def __init__(self, images: List[ImageModel], parent=None):
        """
        Initialize the rename dialog
        
        Args:
            images: List of images to rename
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.images = images
        self.pattern = ""
        
        self.init_ui()
        
        # Load saved pattern from config
        app_settings = Config.get_app_settings()
        saved_pattern = app_settings.get('rename_pattern', '')
        if saved_pattern:
            self.pattern_edit.setText(saved_pattern)
        
        self.update_preview()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Rename Photos")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout()
        
        # Pattern input group
        pattern_group = QGroupBox("Renaming Pattern")
        pattern_layout = QFormLayout()
        
        # Pattern input with save button
        pattern_input_layout = QHBoxLayout()
        
        self.pattern_edit = QLineEdit()
        self.pattern_edit.setPlaceholderText(
            "Example: <Photo_><COUNTER=J{3:2}><_><META=EXIF:DateTimeOriginal>"
        )
        self.pattern_edit.setMinimumWidth(700)  # Make input wider
        self.pattern_edit.textChanged.connect(self.on_pattern_changed)
        pattern_input_layout.addWidget(self.pattern_edit)
        
        # Save pattern button
        self.save_pattern_button = QPushButton()
        self.save_pattern_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogSaveButton))
        self.save_pattern_button.setToolTip("Save pattern to config")
        self.save_pattern_button.setMaximumWidth(40)
        self.save_pattern_button.clicked.connect(self.save_pattern)
        pattern_input_layout.addWidget(self.save_pattern_button)
        
        pattern_layout.addRow("Pattern:", pattern_input_layout)
        
        # Help text
        help_label = QLabel(
            "<b>Pattern Syntax:</b><br>"
            "• Fixed text: &lt;Text&gt; → 'Text'<br>"
            "• Counter: &lt;COUNTER=J{3:2}&gt; → J03, J04, ..., J99, J100... (start at 3, min 2 digits)<br>"
            "• Counter: &lt;COUNTER=M00{1:4}&gt; → M000001, M000002, ... (start at 1, min 4 digits)<br>"
            "• Counter: &lt;COUNTER=ABC{0:1}&gt; → ABC0, ABC1, ..., ABC9, ABC10... (start at 0, min 1 digit)<br>"
            "• Metadata: &lt;META=XMP:CountryCode&gt; → Uses image metadata<br>"
            "• Combine tokens: &lt;Photo_&gt;&lt;COUNTER=J{3:2}&gt;&lt;_&gt;&lt;META=EXIF:DateTimeOriginal&gt;"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: gray; font-size: 10pt;")
        pattern_layout.addRow(help_label)
        
        pattern_group.setLayout(pattern_layout)
        layout.addWidget(pattern_group)
        
        # Preview table
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preview_label)
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(3)
        self.preview_table.setHorizontalHeaderLabels(["Current Filename", "→", "New Filename"])
        self.preview_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.preview_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.preview_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.preview_table.setColumnWidth(1, 30)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.preview_table)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        self.apply_button = QPushButton("Apply Rename")
        self.apply_button.setDefault(True)
        self.apply_button.clicked.connect(self.apply_rename)
        self.apply_button.setEnabled(False)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def on_pattern_changed(self, text: str):
        """Handle pattern text change"""
        self.pattern = text
        self.update_preview()
    
    def save_pattern(self):
        """Save the current pattern to config file"""
        app_settings = Config.get_app_settings()
        app_settings['rename_pattern'] = self.pattern
        Config.set_app_settings(app_settings)
        
        # Show confirmation
        self.statusBar() if hasattr(self, 'statusBar') else None
        QMessageBox.information(
            self,
            "Pattern Saved",
            "Rename pattern has been saved to config."
        )
    
    def parse_pattern(self, pattern: str, image: ImageModel, counter: int) -> str:
        """
        Parse a pattern string and generate filename
        
        Args:
            pattern: Pattern string with tokens
            image: Image to get metadata from
            counter: Current counter value
            
        Returns:
            Generated filename (without extension)
        """
        if not pattern:
            return ""
        
        result = ""
        # Find all tokens in pattern
        tokens = re.findall(r'<([^>]+)>', pattern)
        
        for token in tokens:
            if token.startswith("COUNTER="):
                # Parse counter token: COUNTER=prefix{start:min_digits}
                match = re.match(r'COUNTER=([^{]*)\{(\d+):(\d+)\}', token)
                if match:
                    prefix = match.group(1)  # Fixed prefix
                    start = int(match.group(2))  # Starting index
                    min_digits = int(match.group(3))  # Minimum number of digits
                    
                    # Generate counter value
                    value = start + counter
                    
                    # Format with minimum digits, but allow expansion if needed
                    # max() ensures we use at least min_digits, but more if value requires it
                    actual_digits = max(min_digits, len(str(value)))
                    result += f"{prefix}{value:0{actual_digits}d}"
                else:
                    result += token
            elif token.startswith("META="):
                # Parse metadata token: META=tag
                tag = token[5:]  # Remove "META="
                value = self.get_metadata_value(image, tag)
                result += value if value else ""
            else:
                # Fixed text token
                result += token
        
        return result
    
    def get_metadata_value(self, image: ImageModel, tag: str) -> Optional[str]:
        """
        Get metadata value from image
        
        Args:
            image: Image to get metadata from
            tag: Metadata tag (e.g., "XMP:CountryCode", "EXIF:DateTimeOriginal")
            
        Returns:
            Metadata value or None
        """
        # Normalize tag name
        tag_lower = tag.lower()
        
        # Map common tags to image model attributes
        if "countrycode" in tag_lower:
            # Try to get country code from metadata
            if image.metadata:
                for key in ["XMP:CountryCode", "IPTC:Country-PrimaryLocationCode"]:
                    if key in image.metadata:
                        return str(image.metadata[key])
            return None
        elif "country" in tag_lower:
            return image.country if image.country else None
        elif "city" in tag_lower:
            return image.city if image.city else None
        elif "datetime" in tag_lower or "date" in tag_lower:
            # Try to get from metadata dict if available
            if image.metadata:
                for key in image.metadata:
                    if "datetime" in key.lower() or "createdate" in key.lower():
                        value = str(image.metadata[key])
                        # Clean up datetime format (remove colons, spaces)
                        return value.replace(":", "").replace(" ", "_")
            return None
        
        # Try to get from metadata dict directly
        if image.metadata:
            if tag in image.metadata:
                return str(image.metadata[tag])
        
        return None
    
    def update_preview(self):
        """Update the preview table with new filenames"""
        self.preview_table.setRowCount(len(self.images))
        
        conflicts = {}  # Track duplicate names
        has_error = False
        
        for idx, image in enumerate(self.images):
            # Current filename
            current_name = image.filename
            current_item = QTableWidgetItem(current_name)
            self.preview_table.setItem(idx, 0, current_item)
            
            # Arrow
            arrow_item = QTableWidgetItem("→")
            arrow_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_table.setItem(idx, 1, arrow_item)
            
            # New filename
            if self.pattern:
                new_name_no_ext = self.parse_pattern(self.pattern, image, idx)
                if new_name_no_ext:
                    # Keep original extension
                    ext = Path(current_name).suffix
                    new_name = f"{new_name_no_ext}{ext}"
                    
                    # Track duplicates
                    if new_name in conflicts:
                        conflicts[new_name].append(idx)
                        has_error = True
                    else:
                        conflicts[new_name] = [idx]
                else:
                    new_name = current_name
                    has_error = True
            else:
                new_name = current_name
            
            new_item = QTableWidgetItem(new_name)
            
            # Highlight conflicts
            if new_name in conflicts and len(conflicts[new_name]) > 1:
                new_item.setBackground(Qt.GlobalColor.yellow)
                current_item.setBackground(Qt.GlobalColor.yellow)
            
            self.preview_table.setItem(idx, 2, new_item)
        
        # Update status and button state
        if has_error:
            duplicates = {k: v for k, v in conflicts.items() if len(v) > 1}
            if duplicates:
                self.status_label.setText(
                    f"⚠ Warning: {len(duplicates)} duplicate filename(s) detected!"
                )
            else:
                self.status_label.setText("⚠ Warning: Invalid pattern or missing metadata")
            self.apply_button.setEnabled(False)
        else:
            self.status_label.setText("")
            self.apply_button.setEnabled(True)
    
    def apply_rename(self):
        """Apply the rename operation"""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Rename",
            f"Are you sure you want to rename {len(self.images)} file(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Perform rename
        renamed_count = 0
        errors = []
        
        for idx, image in enumerate(self.images):
            try:
                new_name_no_ext = self.parse_pattern(self.pattern, image, idx)
                if new_name_no_ext:
                    ext = Path(image.filename).suffix
                    new_name = f"{new_name_no_ext}{ext}"
                    
                    # Build new path
                    old_path = image.filepath
                    new_path = old_path.parent / new_name
                    
                    # Rename file
                    if old_path.exists() and old_path != new_path:
                        old_path.rename(new_path)
                        
                        # Also rename ExifTool backup file if it exists
                        old_backup = Path(str(old_path) + "_original")
                        new_backup = Path(str(new_path) + "_original")
                        if old_backup.exists():
                            old_backup.rename(new_backup)
                        
                        # Update image model
                        image.filepath = new_path
                        image.filename = new_name
                        renamed_count += 1
            except Exception as e:
                errors.append(f"{image.filename}: {str(e)}")
        
        # Show results
        if errors:
            QMessageBox.warning(
                self,
                "Rename Completed with Errors",
                f"Renamed {renamed_count} file(s).\n\n"
                f"Errors:\n" + "\n".join(errors[:5])
            )
        else:
            QMessageBox.information(
                self,
                "Rename Completed",
                f"Successfully renamed {renamed_count} file(s)."
            )
        
        self.accept()
    
    def get_renamed_images(self) -> List[ImageModel]:
        """
        Get the list of renamed images
        
        Returns:
            List of image models with updated filenames
        """
        return self.images
