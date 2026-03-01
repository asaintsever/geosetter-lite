"""Quick tester for Geolocation model integration.

Usage:
    python scripts/test_predict_geoloc.py /path/to/image.jpg
"""
import sys
from pathlib import Path

from geosetter_lite.services.ai_service import AIService


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python scripts/test_predict_geoloc.py /path/to/image.jpg")
        return

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        return

    cache_dir = Path.home() / ".cache" / "geosetter_lite"
    ai = AIService(str(cache_dir))

    print("Running prediction...")
    preds = ai.predict_location(image_path, top_k=5)
    print("Predictions (lat, lon, confidence):")
    for lat, lon, conf in preds:
        print(f"  {lat:.6f}, {lon:.6f} ({conf:.4f})")


if __name__ == '__main__':
    main()
