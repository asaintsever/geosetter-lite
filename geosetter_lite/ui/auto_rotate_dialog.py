"""
Auto-rotate dialog - Allow user to auto-rotate images based on EXIF orientation
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QPushButton, QCheckBox, QLabel,
    QScrollArea, QWidget, QHBoxLayout, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QPolygonF
from typing import List
from ..models.image_model import ImageModel
from ..services.exiftool_service import ExifToolService
from .progress_dialog import ProgressDialog
from PIL import Image, ImageOps
import io

class AutoRotateDialog(QDialog):
    """Dialog to auto-rotate images based on EXIF orientation"""

    def __init__(self, images: List[ImageModel], exiftool_service: ExifToolService, parent=None):
        super().__init__(parent)
        self.images = images
        self.exiftool_service = exiftool_service
        self.setWindowTitle("Auto-rotate Photos")
        self.setMinimumSize(800, 600)

        self.image_widgets = []

        self.init_ui()
        self.populate_thumbnails()

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)

        # Select/Deselect All checkbox
        self.select_all_checkbox = QCheckBox("Select/Deselect All")
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)
        main_layout.addWidget(self.select_all_checkbox)

        # Scroll area for thumbnails
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        # Thumbnail container
        self.thumbnail_container = QWidget()
        self.grid_layout = QGridLayout(self.thumbnail_container)
        self.thumbnail_container.setLayout(self.grid_layout)
        scroll_area.setWidget(self.thumbnail_container)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Rotate Selected")


    def populate_thumbnails(self):
        """Populate the grid with image thumbnails"""
        col_count = 5
        images_to_rotate_found = False
        for idx, image_model in enumerate(self.images):
            orientation = None
            if image_model.metadata:
                orientation = image_model.metadata.get('EXIF:Orientation')
            
            if orientation is not None and orientation != 1:
                images_to_rotate_found = True

            thumbnail_widget = self.create_thumbnail_widget(image_model, orientation)
            self.image_widgets.append(thumbnail_widget)
            
            row = idx // col_count
            col = idx % col_count
            self.grid_layout.addWidget(thumbnail_widget, row, col)

        if not images_to_rotate_found:
            self.select_all_checkbox.setChecked(False)
            self.select_all_checkbox.setEnabled(False)


    def create_thumbnail_widget(self, image_model: ImageModel, orientation: int) -> QWidget:
        """Create a widget for a single thumbnail"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Thumbnail label
        pixmap = self.create_thumbnail(image_model.filepath, orientation)
        label = QLabel()
        label.setPixmap(pixmap)
        layout.addWidget(label)

        # Checkbox for selection
        checkbox = QCheckBox(image_model.filename)
        checkbox.setChecked(orientation is not None and orientation != 1)
        layout.addWidget(checkbox)
        
        widget.setProperty("image_model", image_model)
        widget.setProperty("checkbox", checkbox)

        return widget

    def create_thumbnail(self, filepath: Path, orientation: int) -> QPixmap:
        """Create a low-resolution thumbnail for an image, preserving color and avoiding corruption. Do NOT auto-rotate for display."""
        try:
            with Image.open(filepath) as img:
                img.thumbnail((150, 150))
                # Do NOT auto-rotate for display; show as-is
                img_display = img

                # Convert PIL Image to QImage with correct format and stride
                width, height = img_display.size
                if img_display.mode == "RGBA":
                    fmt = QImage.Format.Format_RGBA8888
                    bytes_per_line = width * 4
                else:
                    img_display = img_display.convert("RGB")
                    fmt = QImage.Format.Format_RGB888
                    bytes_per_line = width * 3

                data = img_display.tobytes()
                qt_image = QImage(data, width, height, bytes_per_line, fmt)
                pixmap = QPixmap.fromImage(qt_image)

                if orientation is not None and orientation != 1:
                    # Draw a green triangle with a white tick at the top right corner
                    painter = QPainter(pixmap)
                    try:
                        painter.setRenderHint(QPainter.Antialiasing)
                        triangle_size = 32
                        w, h = pixmap.width(), pixmap.height()
                        # Triangle points (top right corner)
                        points = [
                            QPointF(w, 0),  # top right
                            QPointF(w - triangle_size, 0),  # top left of triangle
                            QPointF(w, triangle_size)  # bottom right of triangle
                        ]

                        poly = QPolygonF(points)
                        painter.setBrush(QColor(0, 128, 0))  # Darker green
                        painter.setPen(Qt.NoPen)
                        painter.drawPolygon(poly)

                        # Draw a bolder, correctly positioned white tick
                        pen = QPen(QColor("white"))
                        pen.setWidth(2)
                        painter.setPen(pen)
                        painter.setBrush(Qt.NoBrush)

                        # Centered points for the tick to be inside the triangle
                        tick_start = QPointF(w - 22, 5)
                        tick_mid = QPointF(w - 14, 13)
                        tick_end = QPointF(w - 8, 9)

                        painter.drawLine(tick_start, tick_mid)
                        painter.drawLine(tick_mid, tick_end)
                    except Exception as paint_exc:
                        print(f"Error painting overlay: {paint_exc}")
                    finally:
                        painter.end()

                return pixmap

        except Exception as e:
            print(f"Error creating thumbnail for {filepath}: {e}")
            return QPixmap(150, 150) # Return a blank pixmap on error
    def on_select_all_changed(self, state):
        """Handle the 'Select/Deselect All' checkbox"""
        is_checked = state == Qt.CheckState.Checked.value
        for widget in self.image_widgets:
            checkbox = widget.property("checkbox")
            checkbox.setChecked(is_checked)

    def on_accept(self):
        """Handle the 'Rotate Selected' button click"""
        selected_images = []
        for widget in self.image_widgets:
            checkbox = widget.property("checkbox")
            if checkbox.isChecked():
                image_model = widget.property("image_model")
                selected_images.append(image_model)

        if not selected_images:
            self.reject()
            return
        
        progress = ProgressDialog("Rotating images...", 0, len(selected_images), self)
        progress.set_message("Starting rotation...")
        progress.show()

        try:
            for i, image_model in enumerate(selected_images):
                progress.set_value(i)
                progress.set_message(f"Rotating {image_model.filename}...")
                
                # 1. Use existing metadata
                metadata = image_model.metadata

                # 2. Rotate image
                with Image.open(image_model.filepath) as img:
                    rotated_img = ImageOps.exif_transpose(img)
                    # 3. Overwrite original file
                    rotated_img.save(image_model.filepath)

                # 4. Prepare metadata for writing, filtering out non-writable composite tags
                writable_metadata = {k: v for k, v in metadata.items() if not k.startswith('Composite:')}
                writable_metadata['EXIF:Orientation'] = 1

                # 5. Write modified metadata back
                self.exiftool_service.write_metadata([image_model.filepath], writable_metadata)

            progress.set_value(len(selected_images))
            QMessageBox.information(self, "Success", f"Successfully rotated {len(selected_images)} images.")
            self.accept()

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"An error occurred during rotation: {e}")
            self.reject()

