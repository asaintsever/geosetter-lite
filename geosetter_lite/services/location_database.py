"""Location database management for geolocation predictions"""

import sqlite3
import csv
from pathlib import Path
from typing import List, Tuple


class LocationDatabase:
    """Manages SQLite database of world locations for geolocation"""
    
    def __init__(self, db_path: Path, csv_path: Path = None):
        """Initialize location database
        
        Args:
            db_path: Path to SQLite database file
            csv_path: Path to CSV file with location data (optional, auto-detected)
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Auto-detect CSV path if not provided
        if csv_path is None:
            # Look for world_locations.csv in multiple locations
            module_dir = Path(__file__).parent.parent  # geosetter_lite package dir
            
            # Priority 1: Check inside package (for installed/built package)
            csv_candidate = module_dir / "data" / "world_locations.csv"
            
            if not csv_candidate.exists():
                # Priority 2: Check project root data directory (for development mode)
                # Go up from geosetter_lite/ to project root
                project_root = module_dir.parent
                csv_candidate = project_root / "data" / "world_locations.csv"
            
            self.csv_path = csv_candidate
        else:
            self.csv_path = csv_path
        
        # Initialize database if it doesn't exist
        if not self.db_path.exists():
            self._initialize_database()
    
    def _initialize_database(self):
        """Create and populate the location database"""
        print(f"Initializing location database at {self.db_path}...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                description TEXT NOT NULL,
                country TEXT,
                city TEXT,
                category TEXT
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_location 
            ON locations(latitude, longitude)
        ''')
        
        # Load locations from CSV file
        locations = self._load_locations_from_csv()
        
        # Populate database
        cursor.executemany(
            'INSERT INTO locations (latitude, longitude, description, country, city, category) VALUES (?, ?, ?, ?, ?, ?)',
            locations
        )
        
        conn.commit()
        conn.close()
        
        print(f"Location database initialized with {len(locations)} locations")
    
    def _load_locations_from_csv(self) -> List[Tuple[float, float, str, str, str, str]]:
        """Load location data from CSV file
        
        Returns:
            List of (lat, lon, description, country, city, category) tuples
            
        Raises:
            FileNotFoundError: If CSV file is not found
            ValueError: If CSV file is invalid or empty
        """
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Location data file not found: {self.csv_path}\n"
                f"Please ensure the world_locations.csv file exists in the data directory."
            )
        
        try:
            locations = []
            
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    locations.append((
                        float(row['latitude']),
                        float(row['longitude']),
                        row['description'],
                        row.get('country', ''),
                        row.get('city', ''),
                        row.get('category', '')
                    ))
            
            if not locations:
                raise ValueError("No locations found in CSV file")
            
            print(f"Loaded {len(locations)} locations from {self.csv_path.name}")
            return locations
            
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid CSV file format: {e}")
    
    def get_all_locations(self) -> List[Tuple[float, float, str]]:
        """Get all locations from database
        
        Returns:
            List of (latitude, longitude, description) tuples
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT latitude, longitude, description FROM locations')
        locations = cursor.fetchall()
        
        conn.close()
        
        return locations
    
    def get_location_count(self) -> int:
        """Get total number of locations in database
        
        Returns:
            Number of locations
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM locations')
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count
    
    def search_by_region(self, min_lat: float, max_lat: float, 
                         min_lon: float, max_lon: float) -> List[Tuple[float, float, str]]:
        """Search locations within a geographic region
        
        Args:
            min_lat: Minimum latitude
            max_lat: Maximum latitude
            min_lon: Minimum longitude
            max_lon: Maximum longitude
            
        Returns:
            List of (latitude, longitude, description) tuples
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT latitude, longitude, description 
            FROM locations 
            WHERE latitude BETWEEN ? AND ? 
            AND longitude BETWEEN ? AND ?
        ''', (min_lat, max_lat, min_lon, max_lon))
        
        locations = cursor.fetchall()
        conn.close()
        
        return locations
