"""
Rotate dialog - Allow user to auto-rotate images based on EXIF orientation or manually rotate any image by 90°
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QPushButton, QCheckBox, QLabel,
    QScrollArea, QWidget, QHBoxLayout, QDialogButtonBox, QMessageBox,
    QToolBar
)
from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QPolygonF, QAction
from typing import List
from ..models.image_model import ImageModel
from ..services.exiftool_service import ExifToolService
from ..services.jpegtran_lossless import jpegtran_lossless_rotate
from .progress_dialog import ProgressDialog
from PIL import Image, ImageOps
import io


class RotateDialog(QDialog):
    """Dialog to auto-rotate images based on EXIF orientation or manually rotate any image by 90°"""

    def _is_jpeg(self, filepath: Path) -> bool:
        return str(filepath).lower().endswith(('.jpg', '.jpeg'))

    def __init__(self, images: List[ImageModel], exiftool_service: ExifToolService, parent=None):
        super().__init__(parent)
        self.images = images
        self.exiftool_service = exiftool_service
        self.setWindowTitle("Rotate Photos")
        self.setMinimumSize(800, 600)

        self.image_widgets = []

        self.init_ui()
        self.populate_thumbnails()

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)

        # Toolbar for rotate actions
        toolbar = QToolBar()
        # Auto-rotate action (EXIF)
        auto_rotate_action = QAction("Auto-rotate (EXIF)", self)
        auto_rotate_action.setToolTip("Auto-rotate selected photos based on EXIF orientation")
        auto_rotate_action.triggered.connect(self.on_auto_rotate_selected)
        toolbar.addAction(auto_rotate_action)
        # Manual rotate 90° action
        rotate_90_action = QAction("Rotate 90°", self)
        rotate_90_action.setToolTip("Rotate selected photos by 90°")
        rotate_90_action.triggered.connect(self.on_rotate_90_selected)
        toolbar.addAction(rotate_90_action)
        main_layout.addWidget(toolbar)

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

        # Dialog buttons (only Cancel)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def on_auto_rotate_selected(self):
        """Auto-rotate selected photos based on EXIF orientation (only those with EXIF:Orientation != 1)"""
        self.rotate_selected_photos(auto=True)

    def on_rotate_90_selected(self):
        """Rotate selected photos by 90° regardless of EXIF orientation"""
        self.rotate_selected_photos(auto=False)

    def rotate_selected_photos(self, auto: bool):
        """Rotate selected photos. If auto=True, only rotate those with EXIF:Orientation != 1. If auto=False, rotate all selected by 90°."""
        selected_widgets = []
        for widget in self.image_widgets:
            checkbox = widget.property("checkbox")
            if checkbox.isChecked():
                selected_widgets.append(widget)

        if not selected_widgets:
            QMessageBox.warning(self, "No Selection", "No photos selected.")
            return

        progress = ProgressDialog("Rotating images...", self)
        progress.set_status("Starting rotation...")
        progress.set_progress(0, len(selected_widgets))
        progress.show()

        try:
            for i, widget in enumerate(selected_widgets):
                if progress.is_cancelled():
                    progress.set_status("Operation cancelled by user.")
                    break

                progress.set_status(f"Rotating image {i+1}/{len(selected_widgets)}...")
                progress.set_progress(i+1, len(selected_widgets))
                image_model = widget.property("image_model")
                metadata = image_model.metadata
                orientation = metadata.get('EXIF:Orientation') if metadata else None
                label = widget.property("thumbnail_label")
                if auto:
                    if orientation is None or orientation == 1:
                        continue  # skip if not auto-rotatable
                    if self._is_jpeg(image_model.filepath):
                        # EXIF auto-rotate is always 90, 180, or 270, but exif_transpose may flip too
                        # For lossless, only rotate if orientation is 6 (90 CW), 8 (270 CW), 3 (180)
                        # Map EXIF orientation to degrees
                        exif_to_degrees = {3: 180, 6: 90, 8: 270}
                        deg = exif_to_degrees.get(orientation)
                        if deg:
                            jpegtran_lossless_rotate(image_model.filepath, deg)
                        else:
                            # fallback to PIL if unknown orientation
                            with Image.open(image_model.filepath) as img:
                                rotated_img = ImageOps.exif_transpose(img)
                                rotated_img.save(image_model.filepath)
                    else:
                        with Image.open(image_model.filepath) as img:
                            rotated_img = ImageOps.exif_transpose(img)
                            rotated_img.save(image_model.filepath)
                else:
                    if self._is_jpeg(image_model.filepath):
                        jpegtran_lossless_rotate(image_model.filepath, 90)
                    else:
                        with Image.open(image_model.filepath) as img:
                            rotated_img = img.rotate(-90, expand=True)
                            rotated_img.save(image_model.filepath)

                # Prepare metadata for writing, filtering out non-writable composite tags
                writable_metadata = {k: v for k, v in metadata.items() if not k.startswith('Composite:')}
                # Use '#' suffix to disable print conversion when writing orientation
                writable_metadata['EXIF:Orientation#'] = 1

                # Write modified metadata back
                self.exiftool_service.write_metadata([image_model.filepath], writable_metadata)

                # Update overlay
                new_pixmap = self.create_thumbnail(image_model.filepath, 1, manually_rotated=not auto)
                label.setPixmap(new_pixmap)

            progress.set_status("Completed rotation.")
            progress.set_progress(len(selected_widgets), len(selected_widgets))
            QMessageBox.information(self, "Success", f"Successfully rotated {len(selected_widgets)} images.")
            progress.close()

            # Re-read metadata only for selected images before refreshing thumbnails
            for widget in selected_widgets:
                image_model = widget.property("image_model")
                image_model.metadata = self.exiftool_service.get_all_tags(image_model.filepath)
                orientation = image_model.metadata.get('EXIF:Orientation') if image_model.metadata else None
                label = widget.property("thumbnail_label")
                pixmap = self.create_thumbnail(image_model.filepath, orientation, manually_rotated=not auto)
                label.setPixmap(pixmap)
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"An error occurred during rotation: {e}")
            self.reject()


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
        pixmap = self.create_thumbnail(image_model.filepath, orientation, manually_rotated=False)
        label = QLabel()
        label.setPixmap(pixmap)
        layout.addWidget(label)

        # Checkbox for selection
        checkbox = QCheckBox(image_model.filename)
        checkbox.setChecked(orientation is not None and orientation != 1)
        layout.addWidget(checkbox)

        widget.setProperty("image_model", image_model)
        widget.setProperty("checkbox", checkbox)
        widget.setProperty("thumbnail_label", label)

        return widget

    def create_thumbnail(self, filepath: Path, orientation: int, manually_rotated: bool = False) -> QPixmap:
        """Create a low-resolution thumbnail for an image, preserving color and avoiding corruption. Do NOT auto-rotate for display."""
        try:
            # Support overlays for EXIF auto-rotatable (green triangle) and manual rotation (blue arrow)
            def _draw_overlays(painter, w, h, orientation, manually_rotated):
                if orientation is not None and orientation != 1 and not manually_rotated:
                    # Green triangle with tick (EXIF auto-rotatable)
                    triangle_size = 32
                    points = [
                        QPointF(w, 0),
                        QPointF(w - triangle_size, 0),
                        QPointF(w, triangle_size)
                    ]
                    poly = QPolygonF(points)
                    painter.setBrush(QColor(0, 128, 0))
                    painter.setPen(Qt.NoPen)
                    painter.drawPolygon(poly)
                    pen = QPen(QColor("white"))
                    pen.setWidth(2)
                    painter.setPen(pen)
                    painter.setBrush(Qt.NoBrush)
                    tick_start = QPointF(w - 22, 5)
                    tick_mid = QPointF(w - 14, 13)
                    tick_end = QPointF(w - 8, 9)
                    painter.drawLine(tick_start, tick_mid)
                    painter.drawLine(tick_mid, tick_end)
                elif manually_rotated:
                    # Blue circular arrow for manual rotation
                    center = QPointF(w - 20, 20)
                    radius = 12
                    pen = QPen(QColor(30, 144, 255))  # Dodger blue
                    pen.setWidth(3)
                    painter.setPen(pen)
                    painter.setBrush(Qt.NoBrush)
                    # Draw arc (3/4 of a circle)
                    painter.drawArc(int(center.x() - radius), int(center.y() - radius), radius * 2, radius * 2, 30 * 16, 300 * 16)
                    # Draw arrow head
                    painter.drawLine(center.x() + radius * 0.7, center.y() - radius * 0.7, center.x() + radius, center.y())
                    painter.drawLine(center.x() + radius * 0.7, center.y() - radius * 0.7, center.x() + radius * 0.3, center.y() - radius * 0.9)

            with Image.open(filepath) as img:
                img.thumbnail((150, 150))
                img_display = img
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

                # Overlay logic
                painter = QPainter(pixmap)
                try:
                    painter.setRenderHint(QPainter.Antialiasing)
                    _draw_overlays(painter, pixmap.width(), pixmap.height(), orientation, manually_rotated)
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
