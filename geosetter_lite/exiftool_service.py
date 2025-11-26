"""
ExifTool Service - Wrapper for reading and writing EXIF/XMP metadata
"""
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import platform


class ExifToolError(Exception):
    """Exception raised when ExifTool operations fail"""
    pass


class ExifToolService:
    """Service for interacting with ExifTool"""
    
    @staticmethod
    def check_availability() -> bool:
        """Check if ExifTool is available on the system"""
        try:
            result = subprocess.run(
                ['exiftool', '-ver'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    @staticmethod
    def read_metadata(filepath: Path) -> Dict[str, Any]:
        """
        Read all EXIF/XMP metadata from an image file
        
        Args:
            filepath: Path to the image file
            
        Returns:
            Dictionary of metadata tags and values
            
        Raises:
            ExifToolError: If reading metadata fails
        """
        try:
            result = subprocess.run(
                ['exiftool', '-j', '-G', '-n', str(filepath)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise ExifToolError(f"ExifTool failed: {result.stderr}")
            
            # Parse JSON output
            data = json.loads(result.stdout)
            if data and len(data) > 0:
                return data[0]
            return {}
            
        except ExifToolError:
            # Re-raise ExifToolError unchanged to avoid double-wrapping
            raise
        except subprocess.TimeoutExpired:
            raise ExifToolError("ExifTool timed out")
        except json.JSONDecodeError as e:
            raise ExifToolError(f"Failed to parse ExifTool output: {e}")
        except Exception as e:
            raise ExifToolError(f"Error reading metadata: {e}")
    
    @staticmethod
    def _preserve_file_times(filepaths: List[Path]) -> Dict[Path, tuple]:
        """
        Get file creation and modification times before metadata write
        
        Args:
            filepaths: List of file paths
            
        Returns:
            Dictionary mapping filepath to (creation_time, modification_time) tuple
        """
        times = {}
        for filepath in filepaths:
            stat = filepath.stat()
            # Get creation time (birth time on macOS/Windows, mtime on Linux)
            if hasattr(stat, 'st_birthtime'):
                creation_time = stat.st_birthtime
            else:
                creation_time = stat.st_mtime  # Fallback for Linux
            modification_time = stat.st_mtime
            times[filepath] = (creation_time, modification_time)
        return times
    
    @staticmethod
    def _restore_file_times(times: Dict[Path, tuple]):
        """
        Restore file creation and modification times after metadata write
        
        Args:
            times: Dictionary mapping filepath to (creation_time, modification_time) tuple
        """
        for filepath, (creation_time, modification_time) in times.items():
            try:
                # Set modification time (this is standard across platforms)
                os.utime(filepath, (modification_time, modification_time))
            except (OSError, PermissionError) as e:
                # If time restoration fails (e.g., permission errors), log but don't fail
                # The metadata write was successful, which is the primary goal
                print(f"Warning: Could not restore file times for {filepath}: {e}")
            
            # On macOS, try to restore creation time using SetFile (if available)
            try:
                if platform.system() == 'Darwin' and hasattr(os.stat(filepath), 'st_birthtime'):
                    # Use touch command with -t flag to set both times
                    # This preserves the birth time on macOS
                    import datetime
                    dt = datetime.datetime.fromtimestamp(creation_time)
                    timestamp_str = dt.strftime('%Y%m%d%H%M.%S')
                    subprocess.run(
                        ['touch', '-t', timestamp_str, str(filepath)],
                        capture_output=True,
                        timeout=5
                    )
            except Exception:
                pass  # If it fails, at least we tried to preserve times
    
    @staticmethod
    def write_metadata(
        filepaths: List[Path],
        metadata: Dict[str, Any],
        overwrite: bool = True,
        preserve_file_dates: bool = True
    ) -> bool:
        """
        Write metadata to one or more image files
        
        Args:
            filepaths: List of paths to image files
            metadata: Dictionary of metadata tags and values to write
            overwrite: If True, overwrite existing metadata values (default: True).
                      If False, only write to tags that don't already exist.
            preserve_file_dates: If True, preserve file creation/modification dates (default: True)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ExifToolError: If writing metadata fails
        """
        if not filepaths:
            return True
        
        # Save original file times if requested
        original_times = None
        if preserve_file_dates:
            original_times = ExifToolService._preserve_file_times(filepaths)
        
        try:
            # Build ExifTool command
            cmd = ['exiftool']
            
            # Add each metadata tag
            for tag, value in metadata.items():
                if value is not None and value != "":
                    # Convert value to string to ensure proper handling
                    value_str = str(value)
                    # Format: -TagName=value (overwrites) or -TagName<=value (only if empty)
                    if overwrite:
                        # For overwrite, use -TAG=VALUE format
                        cmd.append(f'-{tag}={value_str}')
                    else:
                        # For conditional write, use separate -TAG and -TAG<=VALUE format
                        # The <= operator requires the tag and value to be in one argument
                        # but we need to ensure the value is treated as part of the same argument
                        cmd.append(f'-{tag}<={value_str}')
            
            # Add file paths
            cmd.extend([str(fp) for fp in filepaths])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise ExifToolError(f"ExifTool write failed: {result.stderr}")
            
            # Restore original file times if requested
            if preserve_file_dates and original_times:
                ExifToolService._restore_file_times(original_times)
            
            return True
            
        except ExifToolError:
            # Re-raise ExifToolError unchanged to avoid double-wrapping
            raise
        except subprocess.TimeoutExpired:
            raise ExifToolError("ExifTool write timed out")
        except Exception as e:
            raise ExifToolError(f"Error writing metadata: {e}")
    
    @staticmethod
    def get_all_tags(filepath: Path) -> Dict[str, Any]:
        """
        Get all available EXIF/XMP tags with their values
        
        Args:
            filepath: Path to the image file
            
        Returns:
            Dictionary of all metadata tags
        """
        return ExifToolService.read_metadata(filepath)
    
    @staticmethod
    def delete_tag(filepaths: List[Path], tag: str, preserve_file_dates: bool = True) -> bool:
        """
        Delete a specific metadata tag from one or more files
        
        Args:
            filepaths: List of paths to image files
            tag: Tag name to delete
            preserve_file_dates: If True, preserve file creation/modification dates (default: True)
            
        Returns:
            True if successful
            
        Raises:
            ExifToolError: If deletion fails
        """
        if not filepaths:
            return True
        
        # Save original file times if requested
        original_times = None
        if preserve_file_dates:
            original_times = ExifToolService._preserve_file_times(filepaths)
        
        try:
            cmd = ['exiftool', f'-{tag}=']
            cmd.extend([str(fp) for fp in filepaths])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise ExifToolError(f"ExifTool delete failed: {result.stderr}")
            
            # Restore original file times if requested
            if preserve_file_dates and original_times:
                ExifToolService._restore_file_times(original_times)
            
            return True
            
        except ExifToolError:
            # Re-raise ExifToolError unchanged to avoid double-wrapping
            raise
        except subprocess.TimeoutExpired:
            raise ExifToolError("ExifTool delete timed out")
        except Exception as e:
            raise ExifToolError(f"Error deleting tag: {e}")
    
    @staticmethod
    def repair_metadata(filepaths: List[Path], preserve_file_dates: bool = True) -> bool:
        """
        Repair/fix metadata by removing all metadata and copying it back from the original
        This fixes corrupted metadata structures while preserving the actual data
        
        Command: exiftool -all= -tagsfromfile @ -all:all -unsafe -icc_profile <filename>
        
        Args:
            filepaths: List of paths to image files
            preserve_file_dates: If True, preserve file creation/modification dates (default: True)
            
        Returns:
            True if successful
            
        Raises:
            ExifToolError: If repair fails
        """
        if not filepaths:
            return True
        
        # Save original file times if requested
        original_times = None
        if preserve_file_dates:
            original_times = ExifToolService._preserve_file_times(filepaths)
        
        try:
            cmd = [
                'exiftool',
                '-all=',  # Remove all metadata
                '-tagsfromfile', '@',  # Copy from original
                '-all:all',  # Copy all tags
                '-unsafe',  # Allow unsafe tags
                '-icc_profile'  # Preserve ICC profile
            ]
            cmd.extend([str(fp) for fp in filepaths])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # Longer timeout for repair operation
            )
            
            if result.returncode != 0:
                raise ExifToolError(f"ExifTool repair failed: {result.stderr}")
            
            # Restore original file times if requested
            if preserve_file_dates and original_times:
                ExifToolService._restore_file_times(original_times)
            
            return True
            
        except ExifToolError:
            raise
        except subprocess.TimeoutExpired:
            raise ExifToolError("ExifTool repair timed out")
        except Exception as e:
            raise ExifToolError(f"Error repairing metadata: {e}")

