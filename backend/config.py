from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
SOURCE_URL = "https://open-meteo.com/en/docs/historical-weather-api"
CITIES = [
    {"name": "Hyderabad", "latitude": 17.3850, "longitude": 78.4867},
    {"name": "Delhi", "latitude": 28.6139, "longitude": 77.2090},
    {"name": "Mumbai", "latitude": 19.0760, "longitude": 72.8777},
    {"name": "Bengaluru", "latitude": 12.9716, "longitude": 77.5946},
    {"name": "Chennai", "latitude": 13.0827, "longitude": 80.2707},
    {"name": "Kolkata", "latitude": 22.5726, "longitude": 88.3639},
    {"name": "Pune", "latitude": 18.5204, "longitude": 73.8567},
    {"name": "Ahmedabad", "latitude": 23.0225, "longitude": 72.5714},
    {"name": "Jaipur", "latitude": 26.9124, "longitude": 75.7873},
    {"name": "Lucknow", "latitude": 26.8467, "longitude": 80.9462},
]
METRICS = ["temperature", "humidity", "precipitation", "wind_speed"]
