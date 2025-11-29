"""
Map Widget - Display images on an OpenStreetMap using Leaflet
"""
from typing import List, Tuple, Optional
import json
import base64
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl, QObject, Signal, Slot
from PIL import Image
import io


class MapClickHandler(QObject):
    """Handler for map click events"""
    
    clicked = Signal(float, float)  # latitude, longitude
    
    @Slot(float, float)
    def onMapClick(self, lat: float, lng: float):
        """Handle map click from JavaScript"""
        self.clicked.emit(lat, lng)


class MapWidget(QWidget):
    """Widget for displaying a map with image markers"""
    
    # Signal emitted when map is clicked
    map_clicked = Signal(float, float)
    
    def __init__(self, parent=None):
        """Initialize the map widget"""
        super().__init__(parent)
        
        self.markers: List[Tuple[float, float, str, bool, Optional[str]]] = []  # lat, lon, name, is_selected, filepath
        self.active_marker: Optional[Tuple[float, float]] = None
        self.click_handler = MapClickHandler()
        self.click_handler.clicked.connect(self._on_map_clicked)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create web view for displaying the map
        self.web_view = QWebEngineView()
        
        # Set up web channel for JavaScript communication
        self.channel = QWebChannel()
        self.channel.registerObject("clickHandler", self.click_handler)
        self.web_view.page().setWebChannel(self.channel)
        
        layout.addWidget(self.web_view)
        
        self.setLayout(layout)
        
        # Load initial map
        self.load_map()
    
    def _on_map_clicked(self, lat: float, lng: float):
        """Handle map click event"""
        self.active_marker = (lat, lng)
        self.map_clicked.emit(lat, lng)
        self.load_map()  # Reload to show active marker
    
    def load_map(self):
        """Load the OpenStreetMap with Leaflet"""
        html = self._generate_map_html()
        self.web_view.setHtml(html)
    
    def _generate_map_html(self) -> str:
        """
        Generate HTML for the map with Leaflet
        
        Returns:
            HTML string with embedded Leaflet map
        """
        # Define icon creation JavaScript (done once)
        icon_definitions = """
            // Create custom icons
            var blueIcon = L.icon({
                iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
                iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
                shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41],
                className: 'blue-marker'
            });
            
            var greyIcon = L.icon({
                iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
                iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
                shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41],
                className: 'grey-marker'
            });
        """
        
        # Generate markers JavaScript
        markers_js = icon_definitions
        
        # Add regular image markers
        if self.markers:
            for idx, (lat, lon, name, is_selected, filepath) in enumerate(self.markers):
                # Generate popup content with thumbnail
                popup_html = self._generate_popup_html(name, filepath)
                escaped_popup = json.dumps(popup_html)
                
                # Use different icons for selected vs unselected
                icon_var = 'blueIcon' if is_selected else 'greyIcon'
                markers_js += f"""
                L.marker([{lat}, {lon}], {{icon: {icon_var}}}).addTo(map).bindPopup({escaped_popup});
                """
        
        # Add active marker if set
        if self.active_marker:
            lat, lon = self.active_marker
            markers_js += f"""
            var redIcon = L.icon({{
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            }});
            var activeMarker = L.marker([{lat}, {lon}], {{icon: redIcon}}).addTo(map).bindPopup('Active Marker');
            """
        
        # Calculate center and zoom
        all_coords = []
        if self.markers:
            all_coords.extend([(m[0], m[1]) for m in self.markers])
        if self.active_marker:
            all_coords.append(self.active_marker)
        
        if all_coords:
            if len(all_coords) == 1:
                center_lat, center_lon = all_coords[0]
                zoom = 13
            else:
                lats = [c[0] for c in all_coords]
                lons = [c[1] for c in all_coords]
                center_lat = sum(lats) / len(lats)
                center_lon = sum(lons) / len(lons)
                zoom = 10
        else:
            # Default to world view
            center_lat, center_lon = 0, 0
            zoom = 2
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Image Map</title>
            
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
                integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
                crossorigin=""/>
            
            <!-- Leaflet JavaScript -->
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
                integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
                crossorigin=""></script>
            
            <!-- Qt WebChannel -->
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                }}
                #map {{
                    width: 100%;
                    height: 100vh;
                }}
                .leaflet-control-compass {{
                    background: white;
                    padding: 5px;
                    border-radius: 4px;
                    box-shadow: 0 1px 5px rgba(0,0,0,0.4);
                }}
                /* Style for grey (unselected) markers */
                .grey-marker {{
                    filter: grayscale(100%) brightness(0.7);
                    opacity: 0.6;
                }}
                /* Style for blue (selected) markers - keep default appearance */
                .blue-marker {{
                    /* Default Leaflet blue marker */
                }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            
            <script>
                var clickHandler;
                
                // Set up Qt WebChannel
                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    clickHandler = channel.objects.clickHandler;
                }});
                
                // Initialize the map (use window.map for global access)
                window.map = L.map('map').setView([{center_lat}, {center_lon}], {zoom});
                var map = window.map;  // Keep local reference for convenience
                
                // Add OpenStreetMap tile layer
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                    maxZoom: 19
                }}).addTo(map);
                
                // Add compass/scale control
                L.control.scale({{
                    position: 'bottomright',
                    imperial: false
                }}).addTo(map);
                
                // Handle map clicks
                map.on('click', function(e) {{
                    if (clickHandler) {{
                        clickHandler.onMapClick(e.latlng.lat, e.latlng.lng);
                    }}
                }});
                
                // Add markers
                {markers_js}
                
                // Fit bounds if multiple markers
                {self._generate_fit_bounds_js()}
            </script>
        </body>
        </html>
        """
        
        return html
    
    def _generate_fit_bounds_js(self) -> str:
        """Generate JavaScript to fit map bounds to markers"""
        all_coords = []
        if self.markers:
            all_coords.extend([(m[0], m[1]) for m in self.markers])
        if self.active_marker:
            all_coords.append(self.active_marker)
        
        if len(all_coords) > 1:
            lats = [c[0] for c in all_coords]
            lons = [c[1] for c in all_coords]
            
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            
            return f"""
                var bounds = [[{min_lat}, {min_lon}], [{max_lat}, {max_lon}]];
                map.fitBounds(bounds, {{padding: [50, 50]}});
            """
        return ""
    
    def _generate_thumbnail(self, filepath: Optional[str], max_size: int = 150) -> Optional[str]:
        """
        Generate a base64-encoded thumbnail for an image
        
        Args:
            filepath: Path to the image file
            max_size: Maximum width/height for the thumbnail
            
        Returns:
            Base64-encoded image data URL or None if generation fails
        """
        if not filepath:
            return None
        
        try:
            path = Path(filepath)
            if not path.exists():
                return None
            
            # Open and resize image
            with Image.open(path) as img:
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate thumbnail size maintaining aspect ratio
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Save to bytes
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                buffer.seek(0)
                
                # Encode to base64
                img_data = base64.b64encode(buffer.read()).decode('utf-8')
                return f"data:image/jpeg;base64,{img_data}"
        
        except Exception as e:
            print(f"Error generating thumbnail for {filepath}: {e}")
            return None
    
    def _generate_popup_html(self, filename: str, filepath: Optional[str]) -> str:
        """
        Generate HTML content for marker popup with thumbnail
        
        Args:
            filename: Name of the image file
            filepath: Path to the image file
            
        Returns:
            HTML string for the popup
        """
        thumbnail_data = self._generate_thumbnail(filepath)
        
        if thumbnail_data:
            return f"""
                <div style="text-align: center; min-width: 150px;">
                    <img src="{thumbnail_data}" style="max-width: 150px; max-height: 150px; display: block; margin: 0 auto 8px auto; border-radius: 4px;">
                    <div style="font-weight: bold; word-wrap: break-word;">{filename}</div>
                </div>
            """
        else:
            # Fallback to just filename if thumbnail generation fails
            return f"""
                <div style="text-align: center; font-weight: bold;">
                    {filename}
                </div>
            """
    
    def update_markers(self, markers: List[Tuple[float, float, str, bool, Optional[str]]]):
        """
        Update map markers
        
        Args:
            markers: List of tuples (latitude, longitude, name, is_selected, filepath)
        """
        self.markers = markers
        self.load_map()
    
    def clear_markers(self):
        """Clear all markers from the map"""
        self.markers = []
        self.load_map()
    
    def add_marker(self, latitude: float, longitude: float, name: str = "", is_selected: bool = False, filepath: Optional[str] = None):
        """
        Add a single marker to the map
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            name: Optional name/label for the marker
            is_selected: Whether this marker represents a selected image
            filepath: Optional path to the image file for thumbnail generation
        """
        self.markers.append((latitude, longitude, name, is_selected, filepath))
        self.load_map()
    
    def set_active_marker(self, latitude: float, longitude: float):
        """
        Set the active marker position
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
        """
        self.active_marker = (latitude, longitude)
        self.load_map()
    
    def get_active_marker(self) -> Optional[Tuple[float, float]]:
        """
        Get the active marker coordinates
        
        Returns:
            Tuple of (latitude, longitude) or None if no active marker
        """
        return self.active_marker
    
    def clear_active_marker(self):
        """Clear the active marker"""
        self.active_marker = None
        self.load_map()
    
    def set_center(self, latitude: float, longitude: float, zoom: int = 13):
        """
        Set the map center and zoom level
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            zoom: Zoom level (1-19)
        """
        js = f"if (window.map) {{ window.map.setView([{latitude}, {longitude}], {zoom}); }}"
        self.web_view.page().runJavaScript(js)

