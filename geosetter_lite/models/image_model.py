"""
Image Model - Data structure for storing image file information and metadata
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


@dataclass
class ImageModel:
    """Represents an image file with its metadata"""
    
    filepath: Path
    filename: str
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    size: int = 0  # Size in bytes
    
    # EXIF/XMP metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Commonly used metadata fields for quick access
    camera_model: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    sublocation: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    
    # New metadata fields
    headline: Optional[str] = None
    keywords: Optional[List[str]] = field(default_factory=list)
    taken_date: Optional[datetime] = None
    created_date: Optional[datetime] = None
    gps_date: Optional[datetime] = None
    tz_offset: Optional[str] = None  # Format: "+05:00" or "-04:00"
    
    @classmethod
    def from_file(cls, filepath: Path) -> "ImageModel":
        """
        Create an ImageModel from a file path with basic file info
        
        Note: File creation date is only available on macOS/Windows (st_birthtime).
        On Linux/Unix, we use modification time as a fallback since st_ctime 
        represents inode change time, not creation time.
        The actual creation date will be extracted from EXIF metadata if available.
        """
        stat = filepath.stat()
        
        # Get creation date if available (macOS/Windows only)
        # On Linux/Unix, fall back to modification time since st_ctime is inode change time
        if hasattr(stat, 'st_birthtime'):
            creation_date = datetime.fromtimestamp(stat.st_birthtime)
        else:
            # Use modification time as fallback on systems without creation time
            # The actual creation date should come from EXIF metadata
            creation_date = datetime.fromtimestamp(stat.st_mtime)
        
        return cls(
            filepath=filepath,
            filename=filepath.name,
            creation_date=creation_date,
            modification_date=datetime.fromtimestamp(stat.st_mtime),
            size=stat.st_size
        )
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update the metadata dictionary and extract common fields"""
        self.metadata = metadata
        
        # Extract creation date from EXIF if available (more accurate than filesystem)
        exif_date_str = (
            metadata.get('EXIF:DateTimeOriginal') or
            metadata.get('EXIF:CreateDate') or
            metadata.get('XMP:DateCreated')
        )
        if exif_date_str:
            try:
                # Parse EXIF date format: "YYYY:MM:DD HH:MM:SS"
                self.creation_date = datetime.strptime(exif_date_str, "%Y:%m:%d %H:%M:%S")
            except (ValueError, TypeError):
                # Keep the filesystem-based date if EXIF parsing fails
                pass
        
        # Extract common fields with various possible tag names
        # Camera model
        self.camera_model = (
            metadata.get('EXIF:Model') or 
            metadata.get('Model') or
            metadata.get('EXIF:CameraModel')
        )
        
        # Location - Country (check XMP-photoshop first, then IPTC)
        self.country = (
            metadata.get('XMP-photoshop:Country') or
            metadata.get('IPTC:Country-PrimaryLocationName') or
            metadata.get('XMP:Country') or
            metadata.get('IPTC:CountryName')
        )
        
        # Location - City (check XMP-photoshop first, then IPTC)
        self.city = (
            metadata.get('XMP-photoshop:City') or
            metadata.get('IPTC:City') or
            metadata.get('XMP:City') or
            metadata.get('IPTC:LocationName')
        )
        
        # Location - Sublocation (check XMP-iptcCore first, then IPTC)
        self.sublocation = (
            metadata.get('XMP-iptcCore:Location') or
            metadata.get('IPTC:Sub-location') or
            metadata.get('XMP:Location') or
            metadata.get('IPTC:Sublocation')
        )
        
        # GPS Coordinates
        # Use explicit None checks to handle 0 coordinates (equator/prime meridian)
        # Prefer Composite GPS values as they include sign from Ref tags when using -n flag
        gps_lat = metadata.get('Composite:GPSLatitude')
        if gps_lat is None:
            gps_lat = metadata.get('EXIF:GPSLatitude')
        
        gps_lon = metadata.get('Composite:GPSLongitude')
        if gps_lon is None:
            gps_lon = metadata.get('EXIF:GPSLongitude')
        
        # Always update GPS coordinates (set to None if not present)
        if gps_lat is not None:
            self.gps_latitude = self._parse_gps_coordinate(gps_lat)
        else:
            self.gps_latitude = None
        
        if gps_lon is not None:
            self.gps_longitude = self._parse_gps_coordinate(gps_lon)
        else:
            self.gps_longitude = None
        
        # Extract new fields
        # Headline
        self.headline = (
            metadata.get('IPTC:Headline') or
            metadata.get('XMP-photoshop:Headline')
        )
        
        # Keywords - stored as string with * separator, handle both formats
        keywords_raw = (
            metadata.get('IPTC:Keywords') or
            metadata.get('XMP-dc:Subject')
        )
        if keywords_raw:
            if isinstance(keywords_raw, list):
                # Convert array to list for internal storage
                self.keywords = keywords_raw
            elif isinstance(keywords_raw, str):
                # Split by * separator (storage format)
                self.keywords = [k.strip() for k in keywords_raw.split('*') if k.strip()]
            else:
                self.keywords = []
        else:
            self.keywords = []
        
        # Taken Date
        taken_date_str = (
            metadata.get('EXIF:DateTimeOriginal') or
            metadata.get('XMP-exif:DateTimeOriginal')
        )
        if taken_date_str:
            self.taken_date = self._parse_exif_date(taken_date_str)
        else:
            self.taken_date = None
        
        # Created Date
        created_date_str = (
            metadata.get('EXIF:CreateDate') or
            metadata.get('XMP-exif:DateTimeDigitized')
        )
        if created_date_str:
            self.created_date = self._parse_exif_date(created_date_str)
        else:
            self.created_date = None
        
        # Auto-set Created Date from Taken Date if Created Date is missing
        if self.taken_date and not self.created_date:
            self.created_date = self.taken_date
        
        # GPS Date - combine GPSDateStamp and GPSTimeStamp
        gps_date_stamp = metadata.get('EXIF:GPSDateStamp')
        gps_time_stamp = metadata.get('EXIF:GPSTimeStamp')
        if gps_date_stamp and gps_time_stamp:
            try:
                # Combine date and time strings
                gps_datetime_str = f"{gps_date_stamp} {gps_time_stamp}"
                self.gps_date = datetime.strptime(gps_datetime_str, "%Y:%m:%d %H:%M:%S")
            except (ValueError, TypeError):
                self.gps_date = None
        else:
            self.gps_date = None
        
        # TZ Offset - prefer OffsetTime format ("+HH:MM"), fallback to TimeZoneOffset
        self.tz_offset = (
            metadata.get('EXIF:OffsetTime') or
            metadata.get('EXIF:OffsetTimeOriginal') or
            metadata.get('EXIF:TimeZoneOffset')
        )
    
    def _parse_exif_date(self, date_str: str) -> Optional[datetime]:
        """Parse EXIF date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # EXIF format: "YYYY:MM:DD HH:MM:SS"
            return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        except (ValueError, TypeError):
            return None
    
    def _parse_gps_coordinate(self, coord: Any) -> Optional[float]:
        """Parse GPS coordinate from various formats to decimal degrees"""
        if coord is None:
            return None
        
        # If already a float, return it
        if isinstance(coord, (int, float)):
            return float(coord)
        
        # If it's a string, try to parse it
        if isinstance(coord, str):
            try:
                # Try direct float conversion first
                return float(coord)
            except ValueError:
                # Handle DMS format like "40 deg 26' 46.32\" N"
                # This is a simplified parser - ExifTool usually provides decimal
                pass
        
        return None
    
    def get_gps_string(self) -> str:
        """Get formatted GPS coordinates string"""
        if self.gps_latitude is not None and self.gps_longitude is not None:
            lat_dir = "N" if self.gps_latitude >= 0 else "S"
            lon_dir = "E" if self.gps_longitude >= 0 else "W"
            return f"{abs(self.gps_latitude):.6f}° {lat_dir}, {abs(self.gps_longitude):.6f}° {lon_dir}"
        return ""

