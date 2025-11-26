# World Locations Data

This directory contains the location data used for AI-based geolocation predictions.

## Files

### `world_locations.csv`

This is the primary data source containing 1000+ world locations with their coordinates and descriptions. The SQLite database (`locations.db`) is automatically generated from this file.

**CSV Format:**
```csv
latitude,longitude,description,country,city,category
40.7128,-74.0060,"New York City skyline, skyscrapers, Times Square, Central Park",United States,New York,urban
48.8566,2.3522,"Paris, Eiffel Tower, Seine River, cafes, Haussmann architecture",France,Paris,urban
```

**Columns:**
- `latitude` (required): Latitude coordinate (-90 to 90)
- `longitude` (required): Longitude coordinate (-180 to 180)
- `description` (required): Detailed visual description for AI model (include landmarks, features, architectural style)
- `country` (optional): Country name
- `city` (optional): City name
- `category` (optional): Location category (urban, coastal, mountain, desert, jungle, forest, volcanic, waterfall, wilderness)

## How to Update Locations

### Adding New Locations

1. Open `world_locations.csv` in a text editor or spreadsheet application
2. Add new rows with the required fields
3. Ensure proper CSV formatting (use quotes for descriptions containing commas)
4. Save the file
5. Delete `~/.cache/geosetter_lite/locations.db` to force database rebuild
6. Restart the application

**Example:**
```csv
35.6762,139.6503,"Tokyo, neon lights, skyscrapers, temples, modern city",Japan,Tokyo,urban
```

### Editing Existing Locations

1. Open `world_locations.csv`
2. Modify the desired fields
3. Save the file
4. Delete `~/.cache/geosetter_lite/locations.db`
5. Restart the application

### Removing Locations

1. Open `world_locations.csv`
2. Delete the entire row(s)
3. Save the file
4. Delete `~/.cache/geosetter_lite/locations.db`
5. Restart the application

## Tips for Adding Locations

### Good Descriptions

The AI model uses visual descriptions to match photos with locations. Include:
- **Landmarks**: "Eiffel Tower", "Golden Gate Bridge", "Taj Mahal"
- **Architecture**: "Gothic cathedral", "modern skyscrapers", "colonial buildings"
- **Natural features**: "snow-capped mountains", "tropical beaches", "desert dunes"
- **Vegetation**: "palm trees", "evergreen forests", "rice terraces"
- **Climate indicators**: "tropical", "arid", "snow", "Mediterranean"
- **Urban features**: "canals", "trams", "neon lights", "ancient walls"

### Examples

**Good:**
```csv
48.8566,2.3522,"Paris, Eiffel Tower, Seine River, cafes, Haussmann architecture, cobblestone streets",France,Paris,urban
```

**Too vague:**
```csv
48.8566,2.3522,"European city",France,Paris,urban
```

### Coverage Recommendations

For best geolocation results, include:
- Major cities from all continents
- Famous landmarks and monuments
- Natural wonders (mountains, canyons, waterfalls)
- Coastal regions and beaches
- Desert landscapes
- Tropical locations
- Historic sites
- Architectural styles unique to regions

### Categories

Use these standard categories for consistency:
- `urban`: Cities and metropolitan areas
- `coastal`: Beaches, ports, seaside locations
- `mountain`: Mountain ranges, alpine regions
- `desert`: Arid landscapes, sand dunes
- `jungle`: Tropical rainforests, dense vegetation
- `forest`: Temperate forests, woodlands
- `volcanic`: Volcanic landscapes, geothermal areas
- `waterfall`: Waterfalls and cascades
- `wilderness`: Remote natural areas

## CSV Formatting Tips

### Handling Commas in Descriptions

Use double quotes around descriptions containing commas:
```csv
40.7128,-74.0060,"New York City, skyscrapers, Times Square",United States,New York,urban
```

### Handling Quotes in Descriptions

Escape quotes by doubling them:
```csv
51.5074,-0.1278,"London, Big Ben, ""The City"", Thames River",United Kingdom,London,urban
```

### Empty Fields

Leave optional fields empty but keep the commas:
```csv
40.7128,-74.0060,"New York City skyline",,New York,urban
```

## Database Management

The SQLite database is automatically created at `~/.cache/geosetter_lite/locations.db` when:
1. The application starts for the first time
2. The database file doesn't exist
3. The application is restarted after deleting the database

**To force a rebuild:**
```bash
rm ~/.cache/geosetter_lite/locations.db
# Then restart the application
```

## Validation

Before using the CSV file, verify:
1. CSV syntax is valid (proper quotes and commas)
2. All locations have required fields (latitude, longitude, description)
3. Coordinates are within valid ranges (-90 to 90 for latitude, -180 to 180 for longitude)
4. Descriptions are detailed and visually descriptive
5. No duplicate entries

## Using Spreadsheet Applications

You can edit the CSV file in Excel, Google Sheets, or LibreOffice Calc:

1. Open the CSV file in your spreadsheet application
2. Edit the data in the spreadsheet
3. Export/Save as CSV (UTF-8 encoding)
4. Ensure the exported file maintains the correct format
5. Delete the database and restart the application

**Note:** Some spreadsheet applications may modify the CSV format. Always verify the file after exporting.

## Current Coverage

The dataset includes 1000+ locations:
- **North America**: 30+ locations (US, Canada, Mexico)
- **Europe**: 80+ locations (Western, Eastern, Scandinavia)
- **Asia**: 100+ locations (East, South, Southeast, Middle East, Central)
- **Africa**: 50+ locations (North, Sub-Saharan, West, Southern)
- **South America**: 40+ locations (Brazil, Argentina, Chile, Colombia, Peru)
- **Oceania**: 15+ locations (Australia, New Zealand, Pacific Islands)
- **Landmarks**: 20+ natural and historic sites

## Contributing

When adding new locations:
1. Research the location to ensure accurate coordinates
2. Write detailed, visually descriptive text
3. Include multiple visual cues (architecture, landscape, landmarks)
4. Use consistent formatting and categories
5. Test the geolocation feature with sample photos
