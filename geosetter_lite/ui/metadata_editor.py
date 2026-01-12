"""
Metadata Editor Dialog - Edit EXIF/XMP metadata for images
"""
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QLineEdit, QWidget, QMenu
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent, QColor
from ..services.exiftool_service import ExifToolService, ExifToolError
from .table_delegates import CountryDelegate


class MetadataEditor(QDialog):
    """Dialog for editing EXIF/XMP metadata"""
    
    def __init__(self, filepaths: List[Path], exiftool_service: ExifToolService, parent=None):
        """
        Initialize the metadata editor
        
        Args:
            filepaths: List of image file paths to edit
            exiftool_service: ExifTool service instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.filepaths = filepaths
        self.exiftool_service = exiftool_service
        self.metadata = {}
        self.all_metadata_rows = []  # Store all rows for filtering
        self.original_values = {}  # Store original values to detect changes
        self.modified_tags = set()  # Track modified tags
        self.added_tags = set()  # Track added tags
        
        self.setWindowTitle("Edit Metadata")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        
        self.init_ui()
        self.load_metadata()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Header label
        if len(self.filepaths) == 1:
            header_text = f"Editing metadata for: {self.filepaths[0].name}"
        else:
            header_text = f"Editing metadata for {len(self.filepaths)} images"
        
        header_label = QLabel(header_text)
        header_label.setStyleSheet("font-weight: bold; font-size: 12pt; padding: 10px;")
        layout.addWidget(header_label)
        
        # Filter field
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:")
        filter_layout.addWidget(filter_label)
        
        self.filter_field = QLineEdit()
        self.filter_field.setPlaceholderText("Type to filter metadata tags...")
        self.filter_field.textChanged.connect(self.filter_metadata)
        self.filter_field.setClearButtonEnabled(True)
        filter_layout.addWidget(self.filter_field)
        
        layout.addLayout(filter_layout)
        
        # Info label for multiple images
        if len(self.filepaths) > 1:
            info_label = QLabel(
                "Changes will be applied to all selected images. "
                "Empty values will not overwrite existing metadata."
            )
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: #666; padding: 5px 10px;")
            layout.addWidget(info_label)
        
        # Metadata table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Tag Name", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Connect to cell changed signal to track modifications
        self.table.itemChanged.connect(self.on_cell_changed)
        
        # Install event filter for Delete key
        self.table.installEventFilter(self)
        
        layout.addWidget(self.table)
        
        # Add tag button
        add_tag_layout = QHBoxLayout()
        add_tag_layout.addStretch()
        
        self.add_tag_button = QPushButton("Add New Tag")
        self.add_tag_button.clicked.connect(self.add_new_tag)
        add_tag_layout.addWidget(self.add_tag_button)
        
        layout.addLayout(add_tag_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.setDefault(True)
        self.apply_button.clicked.connect(self.apply_changes)
        button_layout.addWidget(self.apply_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_metadata(self):
        """Load metadata from the first image"""
        if not self.filepaths:
            return
        
        try:
            # Load metadata from the first image
            self.metadata = self.exiftool_service.read_metadata(self.filepaths[0])
            
            # Populate table
            self.populate_table()
            
        except ExifToolError as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to load metadata: {str(e)}"
            )
    
    def populate_table(self):
        """Populate the table with metadata"""
        # Filter out some system tags that shouldn't be edited
        excluded_prefixes = ['File:', 'System:', 'SourceFile', 'ExifTool']
        
        filtered_metadata = {
            k: v for k, v in self.metadata.items()
            if not any(k.startswith(prefix) for prefix in excluded_prefixes)
        }
        
        # Store original values for change detection
        self.original_values = {k: str(v) if v is not None else "" for k, v in filtered_metadata.items()}
        
        # Store all metadata rows for filtering
        self.all_metadata_rows = sorted(filtered_metadata.items())
        
        # Display all rows initially
        self.display_filtered_rows(self.all_metadata_rows)
    
    def display_filtered_rows(self, rows_to_display):
        """Display the given rows in the table"""
        # Temporarily disconnect itemChanged to avoid triggering on population
        self.table.itemChanged.disconnect(self.on_cell_changed)
        
        self.table.setRowCount(len(rows_to_display))
        
        for row, (tag, value) in enumerate(rows_to_display):
            # Tag name (read-only for existing tags, editable for new tags)
            tag_item = QTableWidgetItem(tag)
            
            # Check if this is a new tag (not in original metadata)
            if tag not in self.original_values:
                # Mark as new tag
                tag_item.setData(Qt.ItemDataRole.UserRole, "new_tag")
            else:
                # Existing tag - make read-only
                tag_item.setFlags(tag_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            self.table.setItem(row, 0, tag_item)
            
            # Value (editable)
            value_str = str(value) if value is not None else ""
            value_item = QTableWidgetItem(value_str)
            self.table.setItem(row, 1, value_item)
            
            # Highlight if modified or added
            if tag in self.modified_tags or tag in self.added_tags:
                self.highlight_row(row)
        
        # Reconnect itemChanged signal
        self.table.itemChanged.connect(self.on_cell_changed)
    
    def filter_metadata(self, filter_text: str):
        """Filter metadata tags based on the filter text"""
        # Build complete list including added tags
        all_rows = list(self.all_metadata_rows)  # Start with original metadata
        
        # Add any new tags that were added by the user
        for tag in self.added_tags:
            # Find the current value for this tag in the table
            for row in range(self.table.rowCount()):
                tag_item = self.table.item(row, 0)
                value_item = self.table.item(row, 1)
                if tag_item and tag_item.text().strip() == tag:
                    value = value_item.text() if value_item else ""
                    # Check if this tag is not already in all_rows
                    if not any(existing_tag == tag for existing_tag, _ in all_rows):
                        all_rows.append((tag, value))
                    break
        
        if not filter_text:
            # No filter - show all rows
            self.display_filtered_rows(all_rows)
        else:
            # Filter rows where tag name or value contains the filter text (case-insensitive)
            filter_lower = filter_text.lower()
            filtered_rows = [
                (tag, value) for tag, value in all_rows
                if filter_lower in tag.lower() or filter_lower in str(value).lower()
            ]
            self.display_filtered_rows(filtered_rows)
    
    def eventFilter(self, obj, event):
        """Event filter to handle Delete key in table"""
        if obj == self.table and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if key_event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self.delete_selected_tags()
                return True  # Event handled
        
        return super().eventFilter(obj, event)
    
    def show_context_menu(self, pos):
        """Show context menu for table"""
        menu = QMenu(self)
        delete_action = menu.addAction("Delete Tag")
        
        action = menu.exec(self.table.mapToGlobal(pos))
        
        if action == delete_action:
            self.delete_selected_tags()
    
    def delete_selected_tags(self):
        """Delete selected tag rows from the table"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            return
        
        # Confirm deletion
        row_count = len(selected_rows)
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {row_count} tag(s)?\n"
            "This will remove the tag(s) from the file when you click Apply.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Sort rows in descending order to delete from bottom to top
            rows_to_delete = sorted([index.row() for index in selected_rows], reverse=True)
            
            for row in rows_to_delete:
                # Get the tag name before deleting
                tag_item = self.table.item(row, 0)
                if tag_item:
                    tag_name = tag_item.text().strip()
                    # If this tag exists in the original metadata, mark it for deletion
                    if tag_name and tag_name in self.metadata:
                        # We'll handle actual deletion in apply_changes by checking for empty values
                        # For now, just remove the row from the table
                        pass
                
                self.table.removeRow(row)
    
    def add_new_tag(self):
        """Add a new tag row to the table"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Empty tag name (editable)
        tag_item = QTableWidgetItem("")
        self.table.setItem(row, 0, tag_item)
        
        # Empty value (editable)
        value_item = QTableWidgetItem("")
        self.table.setItem(row, 1, value_item)
        
        # Mark as new row (will be tracked when values are entered)
        tag_item.setData(Qt.ItemDataRole.UserRole, "new_tag")
        
        # Scroll to the new row
        self.table.scrollToItem(tag_item)
        self.table.editItem(tag_item)
    
    def on_cell_changed(self, item: QTableWidgetItem):
        """Handle cell value changes to track modifications"""
        if item.column() != 1:  # Only track value column changes
            return
        
        row = item.row()
        tag_item = self.table.item(row, 0)
        
        if not tag_item:
            return
        
        tag = tag_item.text().strip()
        if not tag:
            return
        
        current_value = item.text()  # Don't strip - compare as-is
        
        # Check if this is a new tag
        is_new_tag = tag_item.data(Qt.ItemDataRole.UserRole) == "new_tag"
        
        if is_new_tag:
            # New tag with value
            if current_value.strip():  # Check if non-empty after stripping
                self.added_tags.add(tag)
                self.highlight_row(row)
            else:
                # New tag with empty value - remove highlight
                self.added_tags.discard(tag)
                self.unhighlight_row(row)
        else:
            # Existing tag - check if modified
            original_value = self.original_values.get(tag, "")
            if current_value != original_value:
                self.modified_tags.add(tag)
                self.highlight_row(row)
            else:
                # Value restored to original
                self.modified_tags.discard(tag)
                self.unhighlight_row(row)
    
    def highlight_row(self, row: int):
        """Highlight a row to indicate it has been modified or added"""
        # Light yellow/cream color for modified rows
        highlight_color = QColor(255, 252, 220)
        text_color = QColor(0, 0, 0)  # Black text
        
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(highlight_color)
                item.setForeground(text_color)
    
    def unhighlight_row(self, row: int):
        """Remove highlight from a row"""
        # Reset to default - let Qt handle alternating colors
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setData(Qt.ItemDataRole.BackgroundRole, None)  # Clear background
                item.setData(Qt.ItemDataRole.ForegroundRole, None)  # Clear foreground
    
    def _get_country_code_for_name(self, country_name: str) -> Optional[str]:
        """Get ISO country code for a country name"""
        for code, name in CountryDelegate.COUNTRY_LIST:
            if name.lower() == country_name.lower():
                return code
        return None
    
    def apply_changes(self):
        """Apply metadata changes to all selected images"""
        # Only collect changes for modified and added tags (highlighted rows)
        changes = {}
        tags_in_table = set()
        
        for row in range(self.table.rowCount()):
            tag_item = self.table.item(row, 0)
            value_item = self.table.item(row, 1)
            
            if tag_item and value_item:
                tag = tag_item.text().strip()
                value = value_item.text().strip()
                
                if tag:
                    tags_in_table.add(tag)
                    
                    # Only include tags that were modified or added
                    if tag in self.modified_tags or tag in self.added_tags:
                        if value:  # Only include non-empty values
                            changes[tag] = value
                            
                            # Auto-set country code when country name is set
                            if tag in ['IPTC:Country-PrimaryLocationName', 'XMP:Country', 'IPTC:CountryName', 
                                       'XMP-photoshop:Country']:
                                country_code = self._get_country_code_for_name(value)
                                if country_code:
                                    changes['XMP-iptcCore:CountryCode'] = country_code
                                    changes['IPTC:Country-PrimaryLocationCode'] = country_code
        
        # Detect deleted tags (tags that were in original metadata but not in table)
        tags_to_delete = []
        for original_tag in self.metadata.keys():
            # Skip system tags
            if any(original_tag.startswith(prefix) for prefix in ['File:', 'System:', 'SourceFile', 'ExifTool']):
                continue
            
            if original_tag not in tags_in_table:
                tags_to_delete.append(original_tag)
        
        # Check if there are any changes
        if not changes and not tags_to_delete:
            QMessageBox.information(
                self,
                "No Changes",
                "No metadata changes to apply."
            )
            return
        
        # Apply changes using ExifTool
        try:
            # Write updated/new tags (only modified and added ones)
            if changes:
                self.exiftool_service.write_metadata(self.filepaths, changes)
            
            # Delete removed tags
            if tags_to_delete:
                for tag in tags_to_delete:
                    self.exiftool_service.delete_tag(self.filepaths, tag)
            
            QMessageBox.information(
                self,
                "Success",
                f"Metadata updated successfully for {len(self.filepaths)} image(s).\n"
                f"Modified: {len(changes)} tag(s), Deleted: {len(tags_to_delete)} tag(s)."
            )
            
            self.accept()
            
        except ExifToolError as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update metadata: {str(e)}"
            )

