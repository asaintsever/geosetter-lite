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


# Mapping of ISO 3166-1 alpha-2 (2-letter) to alpha-3 (3-letter) country codes
# This allows us to use the reliable country_code from Nominatim API
ISO_ALPHA2_TO_ALPHA3 = {
    'AF': 'AFG', 'AL': 'ALB', 'DZ': 'DZA', 'AD': 'AND', 'AO': 'AGO', 'AG': 'ATG', 'AR': 'ARG', 
    'AM': 'ARM', 'AU': 'AUS', 'AT': 'AUT', 'AZ': 'AZE', 'BS': 'BHS', 'BH': 'BHR', 'BD': 'BGD',
    'BB': 'BRB', 'BY': 'BLR', 'BE': 'BEL', 'BZ': 'BLZ', 'BJ': 'BEN', 'BT': 'BTN', 'BO': 'BOL',
    'BA': 'BIH', 'BW': 'BWA', 'BR': 'BRA', 'BN': 'BRN', 'BG': 'BGR', 'BF': 'BFA', 'BI': 'BDI',
    'KH': 'KHM', 'CM': 'CMR', 'CA': 'CAN', 'CV': 'CPV', 'CF': 'CAF', 'TD': 'TCD', 'CL': 'CHL',
    'CN': 'CHN', 'CO': 'COL', 'KM': 'COM', 'CG': 'COG', 'CD': 'COD', 'CR': 'CRI', 'CI': 'CIV',
    'HR': 'HRV', 'CU': 'CUB', 'CY': 'CYP', 'CZ': 'CZE', 'DK': 'DNK', 'DJ': 'DJI', 'DM': 'DMA',
    'DO': 'DOM', 'EC': 'ECU', 'EG': 'EGY', 'SV': 'SLV', 'GQ': 'GNQ', 'ER': 'ERI', 'EE': 'EST',
    'ET': 'ETH', 'FJ': 'FJI', 'FI': 'FIN', 'FR': 'FRA', 'GA': 'GAB', 'GM': 'GMB', 'GE': 'GEO',
    'DE': 'DEU', 'GH': 'GHA', 'GR': 'GRC', 'GD': 'GRD', 'GT': 'GTM', 'GN': 'GIN', 'GW': 'GNB',
    'GY': 'GUY', 'HT': 'HTI', 'HN': 'HND', 'HU': 'HUN', 'IS': 'ISL', 'IN': 'IND', 'ID': 'IDN',
    'IR': 'IRN', 'IQ': 'IRQ', 'IE': 'IRL', 'IL': 'ISR', 'IT': 'ITA', 'JM': 'JAM', 'JP': 'JPN',
    'JO': 'JOR', 'KZ': 'KAZ', 'KE': 'KEN', 'KI': 'KIR', 'KP': 'PRK', 'KR': 'KOR', 'KW': 'KWT',
    'KG': 'KGZ', 'LA': 'LAO', 'LV': 'LVA', 'LB': 'LBN', 'LS': 'LSO', 'LR': 'LBR', 'LY': 'LBY',
    'LI': 'LIE', 'LT': 'LTU', 'LU': 'LUX', 'MK': 'MKD', 'MG': 'MDG', 'MW': 'MWI', 'MY': 'MYS',
    'MV': 'MDV', 'ML': 'MLI', 'MT': 'MLT', 'MH': 'MHL', 'MR': 'MRT', 'MU': 'MUS', 'MX': 'MEX',
    'FM': 'FSM', 'MD': 'MDA', 'MC': 'MCO', 'MN': 'MNG', 'ME': 'MNE', 'MA': 'MAR', 'MZ': 'MOZ',
    'MM': 'MMR', 'NA': 'NAM', 'NR': 'NRU', 'NP': 'NPL', 'NL': 'NLD', 'NZ': 'NZL', 'NI': 'NIC',
    'NE': 'NER', 'NG': 'NGA', 'NO': 'NOR', 'OM': 'OMN', 'PK': 'PAK', 'PW': 'PLW', 'PA': 'PAN',
    'PG': 'PNG', 'PY': 'PRY', 'PE': 'PER', 'PH': 'PHL', 'PL': 'POL', 'PT': 'PRT', 'QA': 'QAT',
    'RO': 'ROU', 'RU': 'RUS', 'RW': 'RWA', 'KN': 'KNA', 'LC': 'LCA', 'VC': 'VCT', 'WS': 'WSM',
    'SM': 'SMR', 'ST': 'STP', 'SA': 'SAU', 'SN': 'SEN', 'RS': 'SRB', 'SC': 'SYC', 'SL': 'SLE',
    'SG': 'SGP', 'SK': 'SVK', 'SI': 'SVN', 'SB': 'SLB', 'SO': 'SOM', 'ZA': 'ZAF', 'SS': 'SSD',
    'ES': 'ESP', 'LK': 'LKA', 'SD': 'SDN', 'SR': 'SUR', 'SZ': 'SWZ', 'SE': 'SWE', 'CH': 'CHE',
    'SY': 'SYR', 'TW': 'TWN', 'TJ': 'TJK', 'TZ': 'TZA', 'TH': 'THA', 'TL': 'TLS', 'TG': 'TGO',
    'TO': 'TON', 'TT': 'TTO', 'TN': 'TUN', 'TR': 'TUR', 'TM': 'TKM', 'TV': 'TUV', 'UG': 'UGA',
    'UA': 'UKR', 'AE': 'ARE', 'GB': 'GBR', 'US': 'USA', 'UY': 'URY', 'UZ': 'UZB', 'VU': 'VUT',
    'VA': 'VAT', 'VE': 'VEN', 'VN': 'VNM', 'YE': 'YEM', 'ZM': 'ZMB', 'ZW': 'ZWE'
}


class ReverseGeocodingService:
    """Service for reverse geocoding using Nominatim OpenStreetMap API"""
    
    @staticmethod
    def get_country_code_alpha3(country_code_alpha2: str) -> Optional[str]:
        """
        Convert ISO 3166-1 alpha-2 (2-letter) country code to alpha-3 (3-letter).
        
        Args:
            country_code_alpha2: 2-letter country code from Nominatim API (e.g., 'IT', 'DE', 'US')
            
        Returns:
            3-letter country code (e.g., 'ITA', 'DEU', 'USA') or None if not found
        """
        if not country_code_alpha2:
            return None
        return ISO_ALPHA2_TO_ALPHA3.get(country_code_alpha2.upper())
    
    @staticmethod
    def normalize_country_name(country_name: str) -> str:
        """
        Normalize country name from reverse geocoding API to standard English name.
        
        Note: This is kept as a fallback but prefer using get_country_code_alpha3()
        with the API's country_code for reliable mapping.
        
        Args:
            country_name: Country name from reverse geocoding API
            
        Returns:
            Normalized country name (returns as-is since we now use country codes)
        """
        if not country_name:
            return country_name
        return country_name
    
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
        
        # Extract 2-letter country code and convert to 3-letter
        country_code_alpha2 = address.get('country_code')
        country_code = None
        if country_code_alpha2:
            country_code = ReverseGeocodingService.get_country_code_alpha3(country_code_alpha2)
        
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

