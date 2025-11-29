"""Dialog for displaying and managing similar photos"""

from pathlib import Path
from typing import List, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QCheckBox, QGroupBox, QMessageBox,
    QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PIL import Image
import io


class SimilarityDialog(QDialog):
    """Dialog showing groups of similar photos"""
    
    images_deleted = Signal(list)  # Emits list of deleted file paths
    
    def __init__(self, similarity_groups: List[Tuple[List[Path], float]], parent=None):
        """Initialize similarity dialog
        
        Args:
            similarity_groups: List of (image_paths, similarity_score) tuples
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Similar Photos")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        
        self.similarity_groups = similarity_groups
        self.selected_for_deletion = set()
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Header
        if not self.similarity_groups:
            header_label = QLabel("No similar photos found.")
            header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(header_label)
            
            close_button = QPushButton("Close")
            close_button.clicked.connect(self.reject)
            layout.addWidget(close_button)
            return
        
        header_label = QLabel(f"Found {len(self.similarity_groups)} group(s) of similar photos:")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header_label)
        
        # Scroll area for groups
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Create a group box for each similarity group
        for group_idx, (image_paths, similarity_score) in enumerate(self.similarity_groups):
            group_box = self._create_group_box(group_idx, image_paths, similarity_score)
            scroll_layout.addWidget(group_box)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        info_label = QLabel(f"Selected: 0 photo(s)")
        info_label.setObjectName("info_label")
        self.info_label = info_label
        button_layout.addWidget(info_label)
        
        button_layout.addStretch()
        
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self._delete_selected)
        delete_button.setEnabled(False)
        delete_button.setObjectName("delete_button")
        self.delete_button = delete_button
        button_layout.addWidget(delete_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def _create_group_box(
        self, 
        group_idx: int, 
        image_paths: List[Path], 
        similarity_score: float
    ) -> QGroupBox:
        """Create a group box for a set of similar images
        
        Args:
            group_idx: Index of the group
            image_paths: List of image paths in the group
            similarity_score: Average similarity score for the group
            
        Returns:
            QGroupBox containing the image thumbnails
        """
        group_box = QGroupBox(f"Group {group_idx + 1} - Similarity: {similarity_score:.2%}")
        group_layout = QVBoxLayout()
        
        # Grid layout for thumbnails
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # Add thumbnails in a grid (3 columns)
        for idx, image_path in enumerate(image_paths):
            row = idx // 3
            col = idx % 3
            
            thumbnail_widget = self._create_thumbnail_widget(image_path)
            grid_layout.addWidget(thumbnail_widget, row, col)
        
        group_layout.addLayout(grid_layout)
        group_box.setLayout(group_layout)
        
        return group_box
    
    def _create_thumbnail_widget(self, image_path: Path) -> QWidget:
        """Create a widget with thumbnail and checkbox
        
        Args:
            image_path: Path to the image
            
        Returns:
            QWidget containing thumbnail and checkbox
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Thumbnail
        thumbnail_label = QLabel()
        thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail_label.setFixedSize(150, 150)
        thumbnail_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        
        try:
            # Load and resize image
            pixmap = self._load_thumbnail(image_path, 150, 150)
            thumbnail_label.setPixmap(pixmap)
        except Exception as e:
            thumbnail_label.setText(f"Error loading\n{image_path.name}")
            print(f"Error loading thumbnail for {image_path}: {e}")
        
        layout.addWidget(thumbnail_label)
        
        # Filename label
        filename_label = QLabel(image_path.name)
        filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filename_label.setWordWrap(True)
        filename_label.setMaximumWidth(150)
        filename_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(filename_label)
        
        # Checkbox for deletion
        checkbox = QCheckBox("Select for deletion")
        checkbox.setProperty("image_path", str(image_path))
        checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(checkbox)
        
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
        # Open image with PIL
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize maintaining aspect ratio
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        
        # Convert to QPixmap
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.read())
        
        return pixmap
    
    def _on_checkbox_changed(self, state):
        """Handle checkbox state change"""
        checkbox = self.sender()
        image_path = Path(checkbox.property("image_path"))
        
        if state == Qt.CheckState.Checked.value:
            self.selected_for_deletion.add(image_path)
        else:
            self.selected_for_deletion.discard(image_path)
        
        # Update UI
        count = len(self.selected_for_deletion)
        self.info_label.setText(f"Selected: {count} photo(s)")
        self.delete_button.setEnabled(count > 0)
    
    def _delete_selected(self):
        """Delete selected photos after confirmation"""
        if not self.selected_for_deletion:
            return
        
        count = len(self.selected_for_deletion)
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {count} photo(s)?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted_paths = []
            failed_paths = []
            
            for image_path in self.selected_for_deletion:
                try:
                    # Delete the file
                    image_path.unlink()
                    deleted_paths.append(image_path)
                    
                    # Also delete ExifTool backup if it exists
                    backup_path = image_path.parent / f"{image_path.name}_original"
                    if backup_path.exists():
                        backup_path.unlink()
                except Exception as e:
                    print(f"Error deleting {image_path}: {e}")
                    failed_paths.append(image_path)
            
            # Show results
            if failed_paths:
                QMessageBox.warning(
                    self,
                    "Deletion Incomplete",
                    f"Successfully deleted {len(deleted_paths)} photo(s).\n"
                    f"Failed to delete {len(failed_paths)} photo(s)."
                )
            else:
                QMessageBox.information(
                    self,
                    "Deletion Complete",
                    f"Successfully deleted {len(deleted_paths)} photo(s)."
                )
            
            # Emit signal with deleted paths
            if deleted_paths:
                self.images_deleted.emit(deleted_paths)
            
            # Close dialog
            self.accept()

