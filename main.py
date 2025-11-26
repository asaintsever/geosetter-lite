"""
GeoSetter Lite - Image Metadata Viewer and Editor
Main entry point
"""
import sys
import argparse
from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from geosetter_lite.exiftool_service import ExifToolService
from geosetter_lite.main_window import MainWindow
from geosetter_lite.file_scanner import FileScanner


def check_exiftool():
    """Check if ExifTool is available on the system"""
    if not ExifToolService.check_availability():
        QMessageBox.critical(
            None,
            "ExifTool Not Found",
            "ExifTool is not installed or not available in PATH.\n\n"
            "Please install ExifTool:\n"
            "- macOS: brew install exiftool\n"
            "- Linux: sudo apt-get install libimage-exiftool-perl\n"
            "- Windows: Download from https://exiftool.org"
        )
        return False
    return True


def get_image_file() -> Path | None:
    """
    Get image file path from command line or file dialog
    
    Returns:
        Path to the image file or None if cancelled
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Image Metadata Viewer and Editor"
    )
    parser.add_argument(
        'filepath',
        nargs='?',
        type=str,
        help='Path to an image file'
    )
    
    args = parser.parse_args()
    
    # If filepath provided via command line
    if args.filepath:
        filepath = Path(args.filepath)
        
        if not filepath.exists():
            QMessageBox.critical(
                None,
                "File Not Found",
                f"The file does not exist:\n{filepath}"
            )
            return None
        
        if not filepath.is_file():
            QMessageBox.critical(
                None,
                "Invalid File",
                f"The path is not a file:\n{filepath}"
            )
            return None
        
        if not FileScanner.is_supported_image(filepath):
            QMessageBox.critical(
                None,
                "Unsupported Format",
                f"The file is not a supported image format (JPEG/PNG):\n{filepath}"
            )
            return None
        
        return filepath
    
    # Otherwise, show file dialog
    file_dialog = QFileDialog()
    file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    file_dialog.setNameFilter("Images (*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG)")
    file_dialog.setWindowTitle("Select an Image File")
    
    if file_dialog.exec():
        selected_files = file_dialog.selectedFiles()
        if selected_files:
            return Path(selected_files[0])
    
    return None


def main():
    """Main application entry point"""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("GeoSetter Lite")
    app.setOrganizationName("asaintsever")
    
    # Check ExifTool availability
    if not check_exiftool():
        return 1
    
    # Get image file
    image_file = get_image_file()
    
    if not image_file:
        # User cancelled or error occurred
        return 0
    
    # Get parent directory
    directory = image_file.parent
    
    # Create ExifTool service
    exiftool_service = ExifToolService()
    
    # Create and show main window
    window = MainWindow(directory, exiftool_service)
    window.show()
    
    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
