"""
File Scanner - Discover and load images from a directory
"""
from pathlib import Path
from typing import List
from .image_model import ImageModel
from .exiftool_service import ExifToolService, ExifToolError


class FileScanner:
    """Scanner for discovering image files in a directory"""
    
    # Supported image extensions
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    
    def __init__(self, exiftool_service: ExifToolService):
        """
        Initialize the file scanner
        
        Args:
            exiftool_service: ExifTool service instance for reading metadata
        """
        self.exiftool_service = exiftool_service
    
    @staticmethod
    def get_parent_directory(filepath: Path) -> Path:
        """
        Get the parent directory of a file
        
        Args:
            filepath: Path to a file
            
        Returns:
            Path to the parent directory
        """
        return filepath.parent
    
    def scan_directory(self, directory: Path) -> List[ImageModel]:
        """
        Scan a directory for image files and load their metadata
        
        Args:
            directory: Path to the directory to scan
            
        Returns:
            List of ImageModel objects with metadata
        """
        images = []
        
        if not directory.exists() or not directory.is_dir():
            return images
        
        # Find all image files
        for file_path in sorted(directory.iterdir()):
            if file_path.is_file() and file_path.suffix in self.SUPPORTED_EXTENSIONS:
                try:
                    # Create image model with basic file info
                    image = ImageModel.from_file(file_path)
                    
                    # Load metadata using ExifTool
                    try:
                        metadata = self.exiftool_service.read_metadata(file_path)
                        image.update_metadata(metadata)
                        
                        # Auto-write Created Date if it was set from Taken Date
                        if image.taken_date and not metadata.get('EXIF:CreateDate'):
                            try:
                                created_date_str = image.taken_date.strftime('%Y:%m:%d %H:%M:%S')
                                # Concatenate timezone offset to XMP tag if available
                                tz_offset = image.tz_offset or ""
                                xmp_date_str = created_date_str + tz_offset if tz_offset else created_date_str
                                self.exiftool_service.write_metadata(
                                    [file_path],
                                    {
                                        'EXIF:CreateDate': created_date_str,
                                        'XMP-exif:DateTimeDigitized': xmp_date_str
                                    }
                                )
                            except ExifToolError:
                                # Silently ignore if write fails
                                pass
                        
                    except ExifToolError as e:
                        # Continue even if metadata reading fails
                        print(f"Warning: Could not read metadata for {file_path.name}: {e}")
                    
                    images.append(image)
                    
                except Exception as e:
                    print(f"Warning: Could not process {file_path.name}: {e}")
                    continue
        
        return images
    
    @staticmethod
    def is_supported_image(filepath: Path) -> bool:
        """
        Check if a file is a supported image format
        
        Args:
            filepath: Path to the file
            
        Returns:
            True if the file is a supported image format
        """
        return filepath.suffix in FileScanner.SUPPORTED_EXTENSIONS
    
    def scan_from_file(self, filepath: Path) -> List[ImageModel]:
        """
        Scan the parent directory of a given file
        
        Args:
            filepath: Path to an image file
            
        Returns:
            List of ImageModel objects from the parent directory
        """
        parent_dir = self.get_parent_directory(filepath)
        return self.scan_directory(parent_dir)

