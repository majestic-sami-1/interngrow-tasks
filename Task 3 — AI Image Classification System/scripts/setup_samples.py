"""Script to populate assets/samples with sample images for immediate testing."""

from pathlib import Path
import urllib.request
from PIL import Image, ImageDraw

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "assets" / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

# Wikimedia public domain / creative commons sample URLs
SAMPLE_URLS = {
    "golden_retriever.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/BassetHound_profil.jpg/400px-BassetHound_profil.jpg",
    "sports_car.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/2018_Porsche_911_GT3_4.0.jpg/400px-2018_Porsche_911_GT3_4.0.jpg",
    "espresso.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/A_small_cup_of_coffee.JPG/400px-A_small_cup_of_coffee.JPG",
}


def create_fallback_image(filename: str, label: str, bg_color: tuple[int, int, int]):
    """Create a high-contrast fallback image with label text if network download fails."""
    img = Image.new("RGB", (400, 400), color=bg_color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 40, 360, 360], outline=(255, 255, 255), width=4)
    draw.text((100, 190), label, fill=(255, 255, 255))
    target_path = SAMPLES_DIR / filename
    img.save(target_path, format="JPEG", quality=90)
    print(f"Created fallback image at: {target_path}")


def download_or_create_samples():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    colors = {
        "golden_retriever.jpg": ((190, 140, 70), "Basset Hound / Dog"),
        "sports_car.jpg": ((180, 40, 40), "Sports Car"),
        "espresso.jpg": ((60, 40, 30), "Coffee Cup"),
    }

    for filename, url in SAMPLE_URLS.items():
        target_path = SAMPLES_DIR / filename
        if target_path.exists():
            print(f"Sample already exists: {target_path}")
            continue

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                img_data = response.read()
                with open(target_path, "wb") as f:
                    f.write(img_data)
            print(f"Downloaded sample image: {filename}")
        except Exception as e:
            print(f"Could not download {url} ({e}). Generating fallback.")
            color, lbl = colors[filename]
            create_fallback_image(filename, lbl, color)


if __name__ == "__main__":
    download_or_create_samples()
