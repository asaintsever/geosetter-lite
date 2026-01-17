"""
GeoSetter Lite - Image Metadata Viewer and Editor
Main entry point
"""
import sys
import argparse
from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from geosetter_lite.services import ExifToolService, FileScanner
from geosetter_lite.ui import MainWindow


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


def get_directory() -> Path | None:
    """
    Get directory path from command line or directory dialog
    
    Returns:
        Path to the directory or None if cancelled
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Image Metadata Viewer and Editor"
    )
    parser.add_argument(
        'filepath',
        nargs='?',
        type=str,
        help='Path to a directory or image file'
    )
    
    args = parser.parse_args()
    
    # If filepath provided via command line
    if args.filepath:
        filepath = Path(args.filepath)
        
        if not filepath.exists():
            QMessageBox.critical(
                None,
                "Path Not Found",
                f"The path does not exist:\n{filepath}"
            )
            return None
        
        # If it's a file, use its parent directory
        if filepath.is_file():
            if not FileScanner.is_supported_image(filepath):
                QMessageBox.critical(
                    None,
                    "Unsupported Format",
                    f"The file is not a supported image format (JPEG/PNG/HEIF):\n{filepath}"
                )
                return None
            return filepath.parent
        
        # If it's a directory, use it directly
        if filepath.is_dir():
            return filepath
        
        QMessageBox.critical(
            None,
            "Invalid Path",
            f"The path is neither a file nor a directory:\n{filepath}"
        )
        return None
    
    # Otherwise, show directory dialog
    directory = QFileDialog.getExistingDirectory(
        None,
        "Select Directory with Images",
        str(Path.home()),
        QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
    )
    
    if directory:
        return Path(directory)
    
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
    
    # Get directory
    directory = get_directory()
    
    if not directory:
        # User cancelled or error occurred
        return 0
    
    # Create ExifTool service
    exiftool_service = ExifToolService()
    
    # Create and show main window
    window = MainWindow(directory, exiftool_service)
    window.show()
    
    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
