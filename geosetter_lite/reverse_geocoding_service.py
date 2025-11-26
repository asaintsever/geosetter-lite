"""
Reverse Geocoding Service - Convert GPS coordinates to location information
"""
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class GeocodingResult:
    """Result from reverse geocoding"""
    country: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class ReverseGeocodingService:
    """Service for reverse geocoding using Nominatim OpenStreetMap API"""
    
    def __init__(self):
        """Initialize the reverse geocoding service"""
        self.base_url = "https://nominatim.openstreetmap.org/reverse"
        self.user_agent = "ImageGeoSetterLite/1.0"
        self.timeout = 10  # seconds
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[GeocodingResult]:
        """
        Perform reverse geocoding to get location information from coordinates
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            GeocodingResult with location information or None if request fails
        """
        try:
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'addressdetails': 1,
                'zoom': 10  # City level
            }
            
            headers = {
                'User-Agent': self.user_agent
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_response(data)
            else:
                print(f"Reverse geocoding failed with status code: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("Reverse geocoding request timed out")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Reverse geocoding request failed: {e}")
            return None
        except Exception as e:
            print(f"Error during reverse geocoding: {e}")
            return None
    
    def _parse_response(self, data: Dict[str, Any]) -> GeocodingResult:
        """
        Parse Nominatim API response
        
        Args:
            data: JSON response from Nominatim API
            
        Returns:
            GeocodingResult with extracted location information
        """
        address = data.get('address', {})
        
        # Extract country name
        country = address.get('country')
        
        # Note: Nominatim returns 2-letter ISO codes (alpha-2), but we use 3-letter codes (alpha-3)
        # The country_code will be determined by the user's selection in the dialog
        country_code = None
        
        # Extract city (try multiple fields in order of preference)
        city = (
            address.get('city') or
            address.get('town') or
            address.get('village') or
            address.get('municipality') or
            address.get('county') or
            None
        )
        
        return GeocodingResult(
            country=country,
            country_code=country_code,
            city=city,
            raw_data=data
        )

