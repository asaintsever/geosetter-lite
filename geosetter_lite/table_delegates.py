"""
Table Delegates - Custom editors for table columns
"""
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from PySide6.QtWidgets import QStyledItemDelegate, QComboBox, QWidget, QDateTimeEdit
from PySide6.QtCore import Qt, QModelIndex, QDateTime, QEvent


class TimezoneDelegate(QStyledItemDelegate):
    """Delegate for editing timezone with dropdown of all timezones"""
    
    def __init__(self, main_window, parent=None):
        """
        Initialize the delegate
        
        Args:
            main_window: Reference to main window for accessing exiftool service
            parent: Parent widget
        """
        super().__init__(parent)
        self.main_window = main_window
    
    # Comprehensive timezone list with capital cities, major cities, and UTC offsets
    TIMEZONE_LIST = [
        ("UTC", "UTC+00:00 - Coordinated Universal Time"),
        # Americas
        ("America/New_York", "UTC-05:00/-04:00 - New York, Washington D.C., USA (EST/EDT)"),
        ("America/Chicago", "UTC-06:00/-05:00 - Chicago, USA (CST/CDT)"),
        ("America/Denver", "UTC-07:00/-06:00 - Denver, USA (MST/MDT)"),
        ("America/Los_Angeles", "UTC-08:00/-07:00 - Los Angeles, USA (PST/PDT)"),
        ("America/Phoenix", "UTC-07:00 - Phoenix, USA (MST, no DST)"),
        ("America/Anchorage", "UTC-09:00/-08:00 - Anchorage, USA (AKST/AKDT)"),
        ("America/Adak", "UTC-10:00/-09:00 - Adak, Alaska, USA (HST/HDT)"),
        ("Pacific/Honolulu", "UTC-10:00 - Honolulu, Hawaii, USA (HST, no DST)"),
        ("America/Toronto", "UTC-05:00/-04:00 - Toronto, Canada (EST/EDT)"),
        ("America/Vancouver", "UTC-08:00/-07:00 - Vancouver, Canada (PST/PDT)"),
        ("America/Edmonton", "UTC-07:00/-06:00 - Edmonton, Canada (MST/MDT)"),
        ("America/Winnipeg", "UTC-06:00/-05:00 - Winnipeg, Canada (CST/CDT)"),
        ("America/Halifax", "UTC-04:00/-03:00 - Halifax, Canada (AST/ADT)"),
        ("America/St_Johns", "UTC-03:30/-02:30 - St. John's, Canada (NST/NDT)"),
        ("America/Mexico_City", "UTC-06:00/-05:00 - Mexico City, Mexico (CST/CDT)"),
        ("America/Cancun", "UTC-05:00 - Cancun, Mexico (EST, no DST)"),
        ("America/Tijuana", "UTC-08:00/-07:00 - Tijuana, Mexico (PST/PDT)"),
        ("America/Guatemala", "UTC-06:00 - Guatemala City, Guatemala (CST, no DST)"),
        ("America/Belize", "UTC-06:00 - Belmopan, Belize (CST, no DST)"),
        ("America/San_Salvador", "UTC-06:00 - San Salvador, El Salvador (CST, no DST)"),
        ("America/Tegucigalpa", "UTC-06:00 - Tegucigalpa, Honduras (CST, no DST)"),
        ("America/Managua", "UTC-06:00 - Managua, Nicaragua (CST, no DST)"),
        ("America/Costa_Rica", "UTC-06:00 - San José, Costa Rica (CST, no DST)"),
        ("America/Panama", "UTC-05:00 - Panama City, Panama (EST, no DST)"),
        ("America/Havana", "UTC-05:00/-04:00 - Havana, Cuba (CST/CDT)"),
        ("America/Jamaica", "UTC-05:00 - Kingston, Jamaica (EST, no DST)"),
        ("America/Port-au-Prince", "UTC-05:00/-04:00 - Port-au-Prince, Haiti (EST/EDT)"),
        ("America/Santo_Domingo", "UTC-04:00 - Santo Domingo, Dominican Republic (AST, no DST)"),
        ("America/Caracas", "UTC-04:00 - Caracas, Venezuela (VET)"),
        ("America/Bogota", "UTC-05:00 - Bogotá, Colombia (COT)"),
        ("America/Lima", "UTC-05:00 - Lima, Peru (PET)"),
        ("America/Guayaquil", "UTC-05:00 - Quito, Ecuador (ECT)"),
        ("America/La_Paz", "UTC-04:00 - La Paz, Bolivia (BOT)"),
        ("America/Santiago", "UTC-04:00/-03:00 - Santiago, Chile (CLT/CLST)"),
        ("America/Asuncion", "UTC-04:00/-03:00 - Asunción, Paraguay (PYT/PYST)"),
        ("America/Montevideo", "UTC-03:00 - Montevideo, Uruguay (UYT)"),
        ("America/Buenos_Aires", "UTC-03:00 - Buenos Aires, Argentina (ART)"),
        ("America/Sao_Paulo", "UTC-03:00 - Brasília, São Paulo, Brazil (BRT)"),
        ("America/Manaus", "UTC-04:00 - Manaus, Brazil (AMT)"),
        ("America/Fortaleza", "UTC-03:00 - Fortaleza, Brazil (BRT)"),
        # Europe
        ("Europe/London", "UTC+00:00/+01:00 - London, UK (GMT/BST)"),
        ("Europe/Dublin", "UTC+00:00/+01:00 - Dublin, Ireland (GMT/IST)"),
        ("Europe/Lisbon", "UTC+00:00/+01:00 - Lisbon, Portugal (WET/WEST)"),
        ("Europe/Paris", "UTC+01:00/+02:00 - Paris, France (CET/CEST)"),
        ("Europe/Madrid", "UTC+01:00/+02:00 - Madrid, Spain (CET/CEST)"),
        ("Europe/Barcelona", "UTC+01:00/+02:00 - Barcelona, Spain (CET/CEST)"),
        ("Europe/Rome", "UTC+01:00/+02:00 - Rome, Italy (CET/CEST)"),
        ("Europe/Berlin", "UTC+01:00/+02:00 - Berlin, Germany (CET/CEST)"),
        ("Europe/Munich", "UTC+01:00/+02:00 - Munich, Germany (CET/CEST)"),
        ("Europe/Amsterdam", "UTC+01:00/+02:00 - Amsterdam, Netherlands (CET/CEST)"),
        ("Europe/Brussels", "UTC+01:00/+02:00 - Brussels, Belgium (CET/CEST)"),
        ("Europe/Luxembourg", "UTC+01:00/+02:00 - Luxembourg City, Luxembourg (CET/CEST)"),
        ("Europe/Zurich", "UTC+01:00/+02:00 - Bern, Zurich, Switzerland (CET/CEST)"),
        ("Europe/Vienna", "UTC+01:00/+02:00 - Vienna, Austria (CET/CEST)"),
        ("Europe/Prague", "UTC+01:00/+02:00 - Prague, Czech Republic (CET/CEST)"),
        ("Europe/Bratislava", "UTC+01:00/+02:00 - Bratislava, Slovakia (CET/CEST)"),
        ("Europe/Budapest", "UTC+01:00/+02:00 - Budapest, Hungary (CET/CEST)"),
        ("Europe/Warsaw", "UTC+01:00/+02:00 - Warsaw, Poland (CET/CEST)"),
        ("Europe/Copenhagen", "UTC+01:00/+02:00 - Copenhagen, Denmark (CET/CEST)"),
        ("Europe/Stockholm", "UTC+01:00/+02:00 - Stockholm, Sweden (CET/CEST)"),
        ("Europe/Oslo", "UTC+01:00/+02:00 - Oslo, Norway (CET/CEST)"),
        ("Europe/Helsinki", "UTC+02:00/+03:00 - Helsinki, Finland (EET/EEST)"),
        ("Europe/Tallinn", "UTC+02:00/+03:00 - Tallinn, Estonia (EET/EEST)"),
        ("Europe/Riga", "UTC+02:00/+03:00 - Riga, Latvia (EET/EEST)"),
        ("Europe/Vilnius", "UTC+02:00/+03:00 - Vilnius, Lithuania (EET/EEST)"),
        ("Europe/Athens", "UTC+02:00/+03:00 - Athens, Greece (EET/EEST)"),
        ("Europe/Bucharest", "UTC+02:00/+03:00 - Bucharest, Romania (EET/EEST)"),
        ("Europe/Sofia", "UTC+02:00/+03:00 - Sofia, Bulgaria (EET/EEST)"),
        ("Europe/Belgrade", "UTC+01:00/+02:00 - Belgrade, Serbia (CET/CEST)"),
        ("Europe/Zagreb", "UTC+01:00/+02:00 - Zagreb, Croatia (CET/CEST)"),
        ("Europe/Ljubljana", "UTC+01:00/+02:00 - Ljubljana, Slovenia (CET/CEST)"),
        ("Europe/Sarajevo", "UTC+01:00/+02:00 - Sarajevo, Bosnia and Herzegovina (CET/CEST)"),
        ("Europe/Skopje", "UTC+01:00/+02:00 - Skopje, North Macedonia (CET/CEST)"),
        ("Europe/Podgorica", "UTC+01:00/+02:00 - Podgorica, Montenegro (CET/CEST)"),
        ("Europe/Tirana", "UTC+01:00/+02:00 - Tirana, Albania (CET/CEST)"),
        ("Europe/Istanbul", "UTC+03:00 - Ankara, Istanbul, Turkey (TRT, no DST)"),
        ("Europe/Moscow", "UTC+03:00 - Moscow, Russia (MSK, no DST)"),
        ("Europe/Kiev", "UTC+02:00/+03:00 - Kyiv, Ukraine (EET/EEST)"),
        ("Europe/Minsk", "UTC+03:00 - Minsk, Belarus (MSK, no DST)"),
        ("Europe/Chisinau", "UTC+02:00/+03:00 - Chișinău, Moldova (EET/EEST)"),
        ("Europe/Reykjavik", "UTC+00:00 - Reykjavík, Iceland (GMT, no DST)"),
        # Asia
        ("Asia/Dubai", "UTC+04:00 - Abu Dhabi, Dubai, UAE (GST)"),
        ("Asia/Riyadh", "UTC+03:00 - Riyadh, Saudi Arabia (AST)"),
        ("Asia/Kuwait", "UTC+03:00 - Kuwait City, Kuwait (AST)"),
        ("Asia/Bahrain", "UTC+03:00 - Manama, Bahrain (AST)"),
        ("Asia/Qatar", "UTC+03:00 - Doha, Qatar (AST)"),
        ("Asia/Muscat", "UTC+04:00 - Muscat, Oman (GST)"),
        ("Asia/Tehran", "UTC+03:30/+04:30 - Tehran, Iran (IRST/IRDT)"),
        ("Asia/Baghdad", "UTC+03:00 - Baghdad, Iraq (AST)"),
        ("Asia/Jerusalem", "UTC+02:00/+03:00 - Jerusalem, Israel (IST/IDT)"),
        ("Asia/Amman", "UTC+02:00/+03:00 - Amman, Jordan (EET/EEST)"),
        ("Asia/Beirut", "UTC+02:00/+03:00 - Beirut, Lebanon (EET/EEST)"),
        ("Asia/Damascus", "UTC+02:00/+03:00 - Damascus, Syria (EET/EEST)"),
        ("Asia/Kabul", "UTC+04:30 - Kabul, Afghanistan (AFT)"),
        ("Asia/Karachi", "UTC+05:00 - Islamabad, Karachi, Pakistan (PKT)"),
        ("Asia/Kolkata", "UTC+05:30 - New Delhi, Mumbai, India (IST)"),
        ("Asia/Colombo", "UTC+05:30 - Colombo, Sri Lanka (IST)"),
        ("Asia/Kathmandu", "UTC+05:45 - Kathmandu, Nepal (NPT)"),
        ("Asia/Dhaka", "UTC+06:00 - Dhaka, Bangladesh (BST)"),
        ("Asia/Yangon", "UTC+06:30 - Naypyidaw, Yangon, Myanmar (MMT)"),
        ("Asia/Bangkok", "UTC+07:00 - Bangkok, Thailand (ICT)"),
        ("Asia/Vientiane", "UTC+07:00 - Vientiane, Laos (ICT)"),
        ("Asia/Phnom_Penh", "UTC+07:00 - Phnom Penh, Cambodia (ICT)"),
        ("Asia/Ho_Chi_Minh", "UTC+07:00 - Hanoi, Ho Chi Minh City, Vietnam (ICT)"),
        ("Asia/Singapore", "UTC+08:00 - Singapore (SGT)"),
        ("Asia/Kuala_Lumpur", "UTC+08:00 - Kuala Lumpur, Malaysia (MYT)"),
        ("Asia/Jakarta", "UTC+07:00 - Jakarta, Indonesia (WIB)"),
        ("Asia/Manila", "UTC+08:00 - Manila, Philippines (PHT)"),
        ("Asia/Hong_Kong", "UTC+08:00 - Hong Kong (HKT)"),
        ("Asia/Macau", "UTC+08:00 - Macau (CST)"),
        ("Asia/Taipei", "UTC+08:00 - Taipei, Taiwan (CST)"),
        ("Asia/Shanghai", "UTC+08:00 - Beijing, Shanghai, China (CST)"),
        ("Asia/Tokyo", "UTC+09:00 - Tokyo, Japan (JST)"),
        ("Asia/Seoul", "UTC+09:00 - Seoul, South Korea (KST)"),
        ("Asia/Pyongyang", "UTC+09:00 - Pyongyang, North Korea (KST)"),
        ("Asia/Ulaanbaatar", "UTC+08:00 - Ulaanbaatar, Mongolia (ULAT)"),
        # Africa
        ("Africa/Cairo", "UTC+02:00 - Cairo, Egypt (EET)"),
        ("Africa/Tripoli", "UTC+02:00 - Tripoli, Libya (EET)"),
        ("Africa/Tunis", "UTC+01:00 - Tunis, Tunisia (CET)"),
        ("Africa/Algiers", "UTC+01:00 - Algiers, Algeria (CET)"),
        ("Africa/Casablanca", "UTC+00:00/+01:00 - Rabat, Casablanca, Morocco (WET/WEST)"),
        ("Africa/Lagos", "UTC+01:00 - Abuja, Lagos, Nigeria (WAT)"),
        ("Africa/Accra", "UTC+00:00 - Accra, Ghana (GMT)"),
        ("Africa/Dakar", "UTC+00:00 - Dakar, Senegal (GMT)"),
        ("Africa/Abidjan", "UTC+00:00 - Abidjan, Côte d'Ivoire (GMT)"),
        ("Africa/Nairobi", "UTC+03:00 - Nairobi, Kenya (EAT)"),
        ("Africa/Addis_Ababa", "UTC+03:00 - Addis Ababa, Ethiopia (EAT)"),
        ("Africa/Dar_es_Salaam", "UTC+03:00 - Dodoma, Dar es Salaam, Tanzania (EAT)"),
        ("Africa/Kampala", "UTC+03:00 - Kampala, Uganda (EAT)"),
        ("Africa/Kigali", "UTC+02:00 - Kigali, Rwanda (CAT)"),
        ("Africa/Johannesburg", "UTC+02:00 - Pretoria, Johannesburg, South Africa (SAST)"),
        ("Africa/Maputo", "UTC+02:00 - Maputo, Mozambique (CAT)"),
        ("Africa/Harare", "UTC+02:00 - Harare, Zimbabwe (CAT)"),
        ("Africa/Lusaka", "UTC+02:00 - Lusaka, Zambia (CAT)"),
        ("Africa/Windhoek", "UTC+02:00 - Windhoek, Namibia (CAT)"),
        # Australia & Oceania
        ("Australia/Perth", "UTC+08:00 - Perth, Australia (AWST, no DST)"),
        ("Australia/Darwin", "UTC+09:30 - Darwin, Australia (ACST, no DST)"),
        ("Australia/Adelaide", "UTC+09:30/+10:30 - Adelaide, Australia (ACST/ACDT)"),
        ("Australia/Brisbane", "UTC+10:00 - Brisbane, Australia (AEST, no DST)"),
        ("Australia/Sydney", "UTC+10:00/+11:00 - Canberra, Sydney, Australia (AEST/AEDT)"),
        ("Australia/Melbourne", "UTC+10:00/+11:00 - Melbourne, Australia (AEST/AEDT)"),
        ("Australia/Hobart", "UTC+10:00/+11:00 - Hobart, Australia (AEST/AEDT)"),
        ("Pacific/Auckland", "UTC+12:00/+13:00 - Wellington, Auckland, New Zealand (NZST/NZDT)"),
        ("Pacific/Fiji", "UTC+12:00/+13:00 - Suva, Fiji (FJT/FJST)"),
        ("Pacific/Port_Moresby", "UTC+10:00 - Port Moresby, Papua New Guinea (PGT)"),
        ("Pacific/Guam", "UTC+10:00 - Hagåtña, Guam (ChST)"),
        ("Pacific/Pago_Pago", "UTC-11:00 - Pago Pago, American Samoa (SST)"),
        ("Pacific/Tahiti", "UTC-10:00 - Papeete, Tahiti (TAHT)"),
    ]
    
    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QComboBox:
        """Create a combobox editor with all timezones"""
        editor = QComboBox(parent)
        editor.setEditable(False)
        
        # Add all timezones
        for tz_id, tz_display in self.TIMEZONE_LIST:
            editor.addItem(tz_display, tz_id)
        
        return editor
    
    def setEditorData(self, editor: QComboBox, index: QModelIndex):
        """Set the current value in the editor"""
        current_value = index.data(Qt.ItemDataRole.EditRole)
        
        if current_value:
            # Find the timezone in the list
            for i in range(editor.count()):
                if editor.itemData(i) == current_value:
                    editor.setCurrentIndex(i)
                    return
        
        # Default to first item if not found
        editor.setCurrentIndex(0)
    
    def setModelData(self, editor: QComboBox, model, index: QModelIndex):
        """Save the selected timezone back to the model and write to file"""
        tz_id = editor.currentData()
        
        if tz_id is None:
            return
        
        # Set the timezone in the table
        model.setData(index, tz_id, Qt.ItemDataRole.EditRole)
        
        # Get the image for this row and update its metadata in the file
        row = index.row()
        filename_item = self.main_window.table.item(row, 0)
        if filename_item:
            image = filename_item.data(Qt.ItemDataRole.UserRole)
            if image:
                # Write timezone to file using ExifTool
                # Use EXIF:UserComment which is a reliable field for custom text data
                try:
                    metadata = {
                        'EXIF:UserComment': f"Timezone:{tz_id}"
                    }
                    
                    # Calculate TZ offset based on image's taken date or current date
                    reference_date = image.taken_date if image.taken_date else datetime.now()
                    tz_offset = self._calculate_tz_offset(tz_id, reference_date)
                    
                    if tz_offset:
                        metadata['EXIF:TimeZoneOffset'] = tz_offset
                    
                    self.main_window.exiftool_service.write_metadata([image.filepath], metadata)
                    
                    # Update the image model
                    # Note: ImageModel doesn't have a 'timezone' field, only 'tz_offset'
                    if tz_offset:
                        image.tz_offset = tz_offset
                    
                    if not image.metadata:
                        image.metadata = {}
                    image.metadata['EXIF:UserComment'] = f"Timezone:{tz_id}"
                    if tz_offset:
                        image.metadata['EXIF:TimeZoneOffset'] = tz_offset
                    
                    # Update TZ Offset column in the table (column 2)
                    if tz_offset:
                        tz_offset_item = self.main_window.table.item(row, 2)
                        if tz_offset_item:
                            tz_offset_item.setText(tz_offset)
                    
                    self.main_window.statusBar().showMessage(f"Updated timezone for {image.filename}")
                except Exception as e:
                    self.main_window.statusBar().showMessage(f"Error updating timezone: {e}")
    
    def _calculate_tz_offset(self, timezone_id: str, reference_date: datetime) -> Optional[str]:
        """
        Calculate timezone offset for a given timezone at a specific date
        
        Args:
            timezone_id: Timezone identifier (e.g., "America/New_York")
            reference_date: Date to calculate offset for (handles DST)
            
        Returns:
            Offset string in format "+HH:MM" or "-HH:MM", or None if calculation fails
        """
        try:
            tz = ZoneInfo(timezone_id)
            # Create a datetime with the timezone
            dt_with_tz = reference_date.replace(tzinfo=tz)
            # Get offset in format "+0500" or "-0400"
            offset_str = dt_with_tz.strftime('%z')
            # Convert to "+05:00" or "-04:00" format
            if len(offset_str) == 5:  # "+0500" format
                return f"{offset_str[:3]}:{offset_str[3:]}"
            return None
        except Exception:
            return None


class CountryDelegate(QStyledItemDelegate):
    """Delegate for editing country with dropdown of all countries"""
    
    # ICAO 3-letter country codes (ISO 3166-1 alpha-3) with names
    # Comprehensive list of all countries
    COUNTRY_LIST = [
        ("AFG", "Afghanistan"),
        ("ALB", "Albania"),
        ("DZA", "Algeria"),
        ("AND", "Andorra"),
        ("AGO", "Angola"),
        ("ATG", "Antigua and Barbuda"),
        ("ARG", "Argentina"),
        ("ARM", "Armenia"),
        ("AUS", "Australia"),
        ("AUT", "Austria"),
        ("AZE", "Azerbaijan"),
        ("BHS", "Bahamas"),
        ("BHR", "Bahrain"),
        ("BGD", "Bangladesh"),
        ("BRB", "Barbados"),
        ("BLR", "Belarus"),
        ("BEL", "Belgium"),
        ("BLZ", "Belize"),
        ("BEN", "Benin"),
        ("BTN", "Bhutan"),
        ("BOL", "Bolivia"),
        ("BIH", "Bosnia and Herzegovina"),
        ("BWA", "Botswana"),
        ("BRA", "Brazil"),
        ("BRN", "Brunei"),
        ("BGR", "Bulgaria"),
        ("BFA", "Burkina Faso"),
        ("BDI", "Burundi"),
        ("CPV", "Cabo Verde"),
        ("KHM", "Cambodia"),
        ("CMR", "Cameroon"),
        ("CAN", "Canada"),
        ("CAF", "Central African Republic"),
        ("TCD", "Chad"),
        ("CHL", "Chile"),
        ("CHN", "China"),
        ("COL", "Colombia"),
        ("COM", "Comoros"),
        ("COG", "Congo"),
        ("COD", "Congo (Democratic Republic)"),
        ("CRI", "Costa Rica"),
        ("HRV", "Croatia"),
        ("CUB", "Cuba"),
        ("CYP", "Cyprus"),
        ("CZE", "Czech Republic"),
        ("DNK", "Denmark"),
        ("DJI", "Djibouti"),
        ("DMA", "Dominica"),
        ("DOM", "Dominican Republic"),
        ("ECU", "Ecuador"),
        ("EGY", "Egypt"),
        ("SLV", "El Salvador"),
        ("GNQ", "Equatorial Guinea"),
        ("ERI", "Eritrea"),
        ("EST", "Estonia"),
        ("SWZ", "Eswatini"),
        ("ETH", "Ethiopia"),
        ("FJI", "Fiji"),
        ("FIN", "Finland"),
        ("FRA", "France"),
        ("GAB", "Gabon"),
        ("GMB", "Gambia"),
        ("GEO", "Georgia"),
        ("DEU", "Germany"),
        ("GHA", "Ghana"),
        ("GRC", "Greece"),
        ("GRD", "Grenada"),
        ("GTM", "Guatemala"),
        ("GIN", "Guinea"),
        ("GNB", "Guinea-Bissau"),
        ("GUY", "Guyana"),
        ("HTI", "Haiti"),
        ("HND", "Honduras"),
        ("HUN", "Hungary"),
        ("ISL", "Iceland"),
        ("IND", "India"),
        ("IDN", "Indonesia"),
        ("IRN", "Iran"),
        ("IRQ", "Iraq"),
        ("IRL", "Ireland"),
        ("ISR", "Israel"),
        ("ITA", "Italy"),
        ("CIV", "Ivory Coast"),
        ("JAM", "Jamaica"),
        ("JPN", "Japan"),
        ("JOR", "Jordan"),
        ("KAZ", "Kazakhstan"),
        ("KEN", "Kenya"),
        ("KIR", "Kiribati"),
        ("PRK", "Korea (North)"),
        ("KOR", "Korea (South)"),
        ("KWT", "Kuwait"),
        ("KGZ", "Kyrgyzstan"),
        ("LAO", "Laos"),
        ("LVA", "Latvia"),
        ("LBN", "Lebanon"),
        ("LSO", "Lesotho"),
        ("LBR", "Liberia"),
        ("LBY", "Libya"),
        ("LIE", "Liechtenstein"),
        ("LTU", "Lithuania"),
        ("LUX", "Luxembourg"),
        ("MDG", "Madagascar"),
        ("MWI", "Malawi"),
        ("MYS", "Malaysia"),
        ("MDV", "Maldives"),
        ("MLI", "Mali"),
        ("MLT", "Malta"),
        ("MHL", "Marshall Islands"),
        ("MRT", "Mauritania"),
        ("MUS", "Mauritius"),
        ("MEX", "Mexico"),
        ("FSM", "Micronesia"),
        ("MDA", "Moldova"),
        ("MCO", "Monaco"),
        ("MNG", "Mongolia"),
        ("MNE", "Montenegro"),
        ("MAR", "Morocco"),
        ("MOZ", "Mozambique"),
        ("MMR", "Myanmar"),
        ("NAM", "Namibia"),
        ("NRU", "Nauru"),
        ("NPL", "Nepal"),
        ("NLD", "Netherlands"),
        ("NZL", "New Zealand"),
        ("NIC", "Nicaragua"),
        ("NER", "Niger"),
        ("NGA", "Nigeria"),
        ("MKD", "North Macedonia"),
        ("NOR", "Norway"),
        ("OMN", "Oman"),
        ("PAK", "Pakistan"),
        ("PLW", "Palau"),
        ("PSE", "Palestine"),
        ("PAN", "Panama"),
        ("PNG", "Papua New Guinea"),
        ("PRY", "Paraguay"),
        ("PER", "Peru"),
        ("PHL", "Philippines"),
        ("POL", "Poland"),
        ("PRT", "Portugal"),
        ("QAT", "Qatar"),
        ("ROU", "Romania"),
        ("RUS", "Russia"),
        ("RWA", "Rwanda"),
        ("KNA", "Saint Kitts and Nevis"),
        ("LCA", "Saint Lucia"),
        ("VCT", "Saint Vincent and the Grenadines"),
        ("WSM", "Samoa"),
        ("SMR", "San Marino"),
        ("STP", "Sao Tome and Principe"),
        ("SAU", "Saudi Arabia"),
        ("SEN", "Senegal"),
        ("SRB", "Serbia"),
        ("SYC", "Seychelles"),
        ("SLE", "Sierra Leone"),
        ("SGP", "Singapore"),
        ("SVK", "Slovakia"),
        ("SVN", "Slovenia"),
        ("SLB", "Solomon Islands"),
        ("SOM", "Somalia"),
        ("ZAF", "South Africa"),
        ("SSD", "South Sudan"),
        ("ESP", "Spain"),
        ("LKA", "Sri Lanka"),
        ("SDN", "Sudan"),
        ("SUR", "Suriname"),
        ("SWE", "Sweden"),
        ("CHE", "Switzerland"),
        ("SYR", "Syria"),
        ("TWN", "Taiwan"),
        ("TJK", "Tajikistan"),
        ("TZA", "Tanzania"),
        ("THA", "Thailand"),
        ("TLS", "Timor-Leste"),
        ("TGO", "Togo"),
        ("TON", "Tonga"),
        ("TTO", "Trinidad and Tobago"),
        ("TUN", "Tunisia"),
        ("TUR", "Turkey"),
        ("TKM", "Turkmenistan"),
        ("TUV", "Tuvalu"),
        ("UGA", "Uganda"),
        ("UKR", "Ukraine"),
        ("ARE", "United Arab Emirates"),
        ("GBR", "United Kingdom"),
        ("USA", "United States"),
        ("URY", "Uruguay"),
        ("UZB", "Uzbekistan"),
        ("VUT", "Vanuatu"),
        ("VAT", "Vatican City"),
        ("VEN", "Venezuela"),
        ("VNM", "Vietnam"),
        ("YEM", "Yemen"),
        ("ZMB", "Zambia"),
        ("ZWE", "Zimbabwe"),
        # Additional territories
        ("HKG", "Hong Kong"),
        ("MAC", "Macau"),
        ("PRI", "Puerto Rico"),
        ("GUM", "Guam"),
        ("ASM", "American Samoa"),
        ("VIR", "U.S. Virgin Islands"),
        ("GRL", "Greenland"),
        ("NCL", "New Caledonia"),
        ("PYF", "French Polynesia"),
    ]
    
    def __init__(self, main_window, parent=None):
        """
        Initialize the delegate
        
        Args:
            main_window: Reference to main window for updating country code
            parent: Parent widget
        """
        super().__init__(parent)
        self.main_window = main_window
    
    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QComboBox:
        """Create a combobox editor with all countries and filtering"""
        editor = QComboBox(parent)
        editor.setEditable(True)  # Allow typing to filter
        editor.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)  # Don't add new items
        
        # Add all countries sorted by name
        sorted_countries = sorted(self.COUNTRY_LIST, key=lambda x: x[1])
        for code, name in sorted_countries:
            editor.addItem(f"{name} ({code})", (code, name))
        
        # Enable filtering
        editor.completer().setCompletionMode(editor.completer().CompletionMode.PopupCompletion)
        editor.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        
        return editor
    
    def setEditorData(self, editor: QComboBox, index: QModelIndex):
        """Set the current value in the editor"""
        current_value = index.data(Qt.ItemDataRole.EditRole)
        
        if current_value:
            # Try to find by country name
            for i in range(editor.count()):
                code, name = editor.itemData(i)
                if name == current_value or code == current_value:
                    editor.setCurrentIndex(i)
                    return
        
        # Default to first item if not found
        editor.setCurrentIndex(0)
    
    def setModelData(self, editor: QComboBox, model, index: QModelIndex):
        """Save the selected country back to the model, update country code, and write to file"""
        data = editor.currentData()
        
        if data is None:
            return
        
        code, name = data
        
        # Set the country name in the table
        model.setData(index, name, Qt.ItemDataRole.EditRole)
        
        # Get the image for this row and update its metadata in the file
        row = index.row()
        filename_item = self.main_window.table.item(row, 0)
        if filename_item:
            image = filename_item.data(Qt.ItemDataRole.UserRole)
            if image:
                # Write country and country code to file using ExifTool
                # Use correct tag mappings as specified
                try:
                    metadata = {
                        'XMP-photoshop:Country': name,
                        'IPTC:Country-PrimaryLocationName': name,
                        'XMP-iptcCore:CountryCode': code,
                        'IPTC:Country-PrimaryLocationCode': code
                    }
                    self.main_window.exiftool_service.write_metadata([image.filepath], metadata)
                    # Update the image model
                    image.country = name
                    if not image.metadata:
                        image.metadata = {}
                    image.metadata['XMP-photoshop:Country'] = name
                    image.metadata['IPTC:Country-PrimaryLocationName'] = name
                    image.metadata['XMP-iptcCore:CountryCode'] = code
                    image.metadata['IPTC:Country-PrimaryLocationCode'] = code
                    
                    # Auto-add country and country code to keywords
                    self.main_window.update_keywords_with_country(row, name, code)
                    
                    self.main_window.statusBar().showMessage(f"Updated country for {image.filename}")
                except Exception as e:
                    self.main_window.statusBar().showMessage(f"Error updating country: {e}")


class DateTimeDelegate(QStyledItemDelegate):
    """Delegate for editing date/time fields with QDateTimeEdit"""
    
    def __init__(self, main_window, parent=None):
        """
        Initialize the delegate
        
        Args:
            main_window: Reference to main window for accessing exiftool service
            parent: Parent widget
        """
        super().__init__(parent)
        self.main_window = main_window
    
    def editorEvent(self, event, model, option, index):
        """Handle key events - let Delete/Backspace pass through to main window's event filter"""
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                # Let the main window's event filter handle deletion
                return False
        
        return super().editorEvent(event, model, option, index)
    
    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QDateTimeEdit:
        """Create a QDateTimeEdit editor for date/time fields"""
        editor = QDateTimeEdit(parent)
        editor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        editor.setCalendarPopup(True)
        return editor
    
    def setEditorData(self, editor: QDateTimeEdit, index: QModelIndex):
        """Set the current value in the editor"""
        current_value = index.data(Qt.ItemDataRole.EditRole)
        
        if current_value:
            # Try to parse the datetime string
            try:
                # Handle EXIF format "YYYY:MM:DD HH:MM:SS"
                if ':' in current_value and '-' not in current_value:
                    dt = datetime.strptime(current_value, "%Y:%m:%d %H:%M:%S")
                else:
                    # Handle display format "YYYY-MM-DD HH:MM:SS"
                    dt = datetime.strptime(current_value, "%Y-%m-%d %H:%M:%S")
                
                qdt = QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
                editor.setDateTime(qdt)
            except (ValueError, TypeError):
                # If parsing fails, use current datetime
                editor.setDateTime(QDateTime.currentDateTime())
        else:
            editor.setDateTime(QDateTime.currentDateTime())
    
    def setModelData(self, editor: QDateTimeEdit, model, index: QModelIndex):
        """Save the selected datetime back to the model and write to file"""
        qdt = editor.dateTime()
        
        # Convert to Python datetime
        dt = datetime(qdt.date().year(), qdt.date().month(), qdt.date().day(),
                     qdt.time().hour(), qdt.time().minute(), qdt.time().second())
        
        # Format for EXIF (YYYY:MM:DD HH:MM:SS)
        exif_format = dt.strftime("%Y:%m:%d %H:%M:%S")
        
        # Format for display (YYYY-MM-DD HH:MM:SS)
        display_format = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Set the display value in the table
        model.setData(index, display_format, Qt.ItemDataRole.EditRole)
        
        # Get the image for this row and update its metadata in the file
        row = index.row()
        col = index.column()
        filename_item = self.main_window.table.item(row, 0)
        if filename_item:
            image = filename_item.data(Qt.ItemDataRole.UserRole)
            if image:
                # Get timezone offset for XMP tags
                tz_offset = image.tz_offset or ""
                
                # Determine which date field and tags to write
                metadata = {}
                field_name = None
                
                if col == 1:  # Taken Date
                    field_name = 'taken_date'
                    metadata['EXIF:DateTimeOriginal'] = exif_format
                    # Concatenate timezone offset to XMP tag
                    xmp_format = exif_format + tz_offset if tz_offset else exif_format
                    metadata['XMP-exif:DateTimeOriginal'] = xmp_format
                    
                    # Auto-set Created Date from Taken Date if not already set
                    if not image.created_date:
                        metadata['EXIF:CreateDate'] = exif_format
                        metadata['XMP-exif:DateTimeDigitized'] = xmp_format
                        
                elif col == 12:  # Created Date
                    field_name = 'created_date'
                    metadata['EXIF:CreateDate'] = exif_format
                    # Concatenate timezone offset to XMP tag
                    xmp_format = exif_format + tz_offset if tz_offset else exif_format
                    metadata['XMP-exif:DateTimeDigitized'] = xmp_format
                elif col == 9:  # GPS Date
                    field_name = 'gps_date'
                    # GPS Date is always in UTC - user enters UTC time directly
                    # Split into date and time for GPS tags
                    gps_date = dt.strftime("%Y:%m:%d")
                    gps_time = dt.strftime("%H:%M:%S")
                    metadata['EXIF:GPSDateStamp'] = gps_date
                    metadata['EXIF:GPSTimeStamp'] = gps_time
                
                if metadata:
                    try:
                        self.main_window.exiftool_service.write_metadata([image.filepath], metadata)
                        
                        # For GPS Date, read Composite:GPSDateTime and write to XMP-exif:GPSDateTime
                        if col == 9:
                            try:
                                file_metadata = self.main_window.exiftool_service.read_metadata(image.filepath)
                                composite_gps = file_metadata.get('Composite:GPSDateTime')
                                if composite_gps:
                                    self.main_window.exiftool_service.write_metadata(
                                        [image.filepath],
                                        {'XMP-exif:GPSDateTime': composite_gps}
                                    )
                            except Exception:
                                pass  # Silently ignore if composite read/write fails
                        
                        # Update the image model
                        setattr(image, field_name, dt)
                        
                        # If we auto-set Created Date from Taken Date, update the model
                        if col == 1 and not image.created_date:
                            image.created_date = dt
                            # Update the Created Date column in the table
                            created_date_item = self.main_window.table.item(row, 12)
                            if created_date_item:
                                self.main_window.table.blockSignals(True)
                                created_date_item.setText(display_format)
                                self.main_window.table.blockSignals(False)
                        
                        if not image.metadata:
                            image.metadata = {}
                        for tag, value in metadata.items():
                            image.metadata[tag] = value
                        self.main_window.statusBar().showMessage(f"Updated {field_name.replace('_', ' ')} for {image.filename}")
                    except Exception as e:
                        self.main_window.statusBar().showMessage(f"Error updating {field_name}: {e}")


class TZOffsetDelegate(QStyledItemDelegate):
    """Delegate for editing TZ Offset with timezone picker (stores only offset)"""
    
    # Reuse the same timezone list from TimezoneDelegate
    TIMEZONE_LIST = TimezoneDelegate.TIMEZONE_LIST
    
    def __init__(self, main_window, parent=None):
        """
        Initialize the delegate
        
        Args:
            main_window: Reference to main window for accessing exiftool service
            parent: Parent widget
        """
        super().__init__(parent)
        self.main_window = main_window
    
    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QComboBox:
        """Create a QComboBox editor with timezone options"""
        editor = QComboBox(parent)
        editor.setEditable(False)
        
        # Add timezone options (display with zone ID, city names and offsets)
        for tz_id, tz_display in self.TIMEZONE_LIST:
            # Format: "America/New_York - UTC-05:00/-04:00 - New York, Washington D.C., USA (EST/EDT)"
            display_with_zone = f"{tz_id} - {tz_display}"
            editor.addItem(display_with_zone, tz_id)
        
        return editor
    
    def setEditorData(self, editor: QComboBox, index: QModelIndex):
        """Set the current value in the editor"""
        current_offset = index.data(Qt.ItemDataRole.EditRole)
        
        # Try to find a matching timezone for the current offset
        # This is approximate since multiple timezones can have the same offset
        if current_offset:
            # Find first timezone that matches this offset (approximate)
            for i, (tz_id, tz_display) in enumerate(self.TIMEZONE_LIST):
                if current_offset in tz_display:
                    editor.setCurrentIndex(i)
                    return
        
        # Default to UTC if no match
        editor.setCurrentIndex(0)
    
    def setModelData(self, editor: QComboBox, model, index: QModelIndex):
        """Save the selected timezone offset back to the model and write to file"""
        timezone_id = editor.currentData()
        
        if not timezone_id:
            return
        
        # Get the image for this row to use its taken_date for offset calculation
        row = index.row()
        filename_item = self.main_window.table.item(row, 0)
        if not filename_item:
            return
        
        image = filename_item.data(Qt.ItemDataRole.UserRole)
        if not image:
            return
        
        # Calculate offset from timezone ID and taken_date
        reference_date = image.taken_date if image.taken_date else datetime.now()
        offset_str = self._calculate_offset(timezone_id, reference_date)
        
        if offset_str:
            # Convert "+HH:MM" to decimal hours for EXIF:TimeZoneOffset
            try:
                # Parse "+05:00" or "-04:30" format
                sign = 1 if offset_str[0] == '+' else -1
                hours = int(offset_str[1:3])
                minutes = int(offset_str[4:6])
                # TimeZoneOffset is in hours (can be fractional)
                tz_offset_hours = sign * (hours + minutes / 60.0)
            except (ValueError, IndexError):
                tz_offset_hours = 0
            
            # Write to multiple EXIF tags
            metadata = {
                'EXIF:TimeZoneOffset': str(tz_offset_hours),
                'EXIF:OffsetTime': offset_str,
                'EXIF:OffsetTimeOriginal': offset_str,
                'EXIF:OffsetTimeDigitized': offset_str
            }
            
            # Update XMP date tags to include the new timezone offset
            if image.taken_date:
                taken_date_str = image.taken_date.strftime('%Y:%m:%d %H:%M:%S')
                metadata['XMP-exif:DateTimeOriginal'] = taken_date_str + offset_str
                
                # Recalculate GPS Date in UTC based on Taken Date and new offset
                if image.gps_date:
                    # Convert Taken Date (local time) to UTC
                    gps_utc = self._convert_to_utc(image.taken_date, offset_str)
                    if gps_utc:
                        gps_date_str = gps_utc.strftime('%Y:%m:%d')
                        gps_time_str = gps_utc.strftime('%H:%M:%S')
                        metadata['EXIF:GPSDateStamp'] = gps_date_str
                        metadata['EXIF:GPSTimeStamp'] = gps_time_str
                        # Update image model
                        image.gps_date = gps_utc
            
            if image.created_date:
                created_date_str = image.created_date.strftime('%Y:%m:%d %H:%M:%S')
                metadata['XMP-exif:DateTimeDigitized'] = created_date_str + offset_str
            
            try:
                self.main_window.exiftool_service.write_metadata([image.filepath], metadata)
                
                # If GPS Date was recalculated, read Composite:GPSDateTime and write to XMP-exif:GPSDateTime
                if image.gps_date and image.taken_date:
                    try:
                        file_metadata = self.main_window.exiftool_service.read_metadata(image.filepath)
                        composite_gps = file_metadata.get('Composite:GPSDateTime')
                        if composite_gps:
                            self.main_window.exiftool_service.write_metadata(
                                [image.filepath],
                                {'XMP-exif:GPSDateTime': composite_gps}
                            )
                    except Exception:
                        pass  # Silently ignore if composite read/write fails
                
                # Update the image model
                image.tz_offset = offset_str
                if not image.metadata:
                    image.metadata = {}
                image.metadata['EXIF:OffsetTime'] = offset_str
                image.metadata['EXIF:TimeZoneOffset'] = str(tz_offset_hours)
                if image.taken_date:
                    image.metadata['XMP-exif:DateTimeOriginal'] = taken_date_str + offset_str
                if image.created_date:
                    image.metadata['XMP-exif:DateTimeDigitized'] = created_date_str + offset_str
                
                # Update the table cells
                self.main_window.table.blockSignals(True)
                
                # Update TZ Offset column
                col = index.column()
                tz_offset_item = self.main_window.table.item(row, col)
                if tz_offset_item:
                    tz_offset_item.setText(offset_str)
                
                # Update GPS Date column if it was recalculated
                if image.gps_date and image.taken_date:
                    gps_date_item = self.main_window.table.item(row, 9)
                    if gps_date_item:
                        from .utils import format_date
                        gps_date_item.setText(format_date(image.gps_date) if image.gps_date else "")
                
                self.main_window.table.blockSignals(False)
                
                self.main_window.statusBar().showMessage(f"Updated TZ Offset for {image.filename}")
            except Exception as e:
                self.main_window.statusBar().showMessage(f"Error updating TZ Offset: {e}")
    
    def _calculate_offset(self, timezone_id: str, reference_date: datetime) -> Optional[str]:
        """
        Calculate UTC offset for a timezone at a specific date
        
        Args:
            timezone_id: Timezone identifier (e.g., "America/New_York")
            reference_date: Date to calculate offset for (handles DST)
            
        Returns:
            Offset string in format "+HH:MM" or "-HH:MM", or None if calculation fails
        """
        try:
            tz = ZoneInfo(timezone_id)
            # Create a datetime with the timezone
            dt_with_tz = reference_date.replace(tzinfo=tz)
            # Get the offset
            offset = dt_with_tz.strftime('%z')  # Returns format like "+0500" or "-0400"
            if offset:
                # Convert to "+05:00" format
                return f"{offset[:3]}:{offset[3:]}"
            return None
        except Exception:
            return None
    
    def _convert_to_utc(self, local_dt: datetime, offset_str: str) -> Optional[datetime]:
        """
        Convert a local datetime to UTC using the given offset
        
        Args:
            local_dt: Local datetime
            offset_str: Offset string in format "+HH:MM" or "-HH:MM"
            
        Returns:
            UTC datetime, or None if conversion fails
        """
        try:
            # Parse offset string
            sign = 1 if offset_str[0] == '+' else -1
            hours = int(offset_str[1:3])
            minutes = int(offset_str[4:6])
            offset_seconds = sign * (hours * 3600 + minutes * 60)
            
            # Convert to UTC by subtracting the offset
            from datetime import timedelta
            utc_dt = local_dt - timedelta(seconds=offset_seconds)
            return utc_dt
        except Exception:
            return None

