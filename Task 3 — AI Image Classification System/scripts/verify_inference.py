import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PIL import Image
from src.classifier import get_classifier

def verify():
    clf = get_classifier()
    samples = [
        "assets/samples/golden_retriever.jpg",
        "assets/samples/sports_car.jpg",
        "assets/samples/espresso.jpg",
    ]

    for sample_path in samples:
        img = Image.open(sample_path)
        predictions, latency = clf.predict(img, top_k=3)
        print(f"\n--- {sample_path} ({latency:.1f}ms) ---")
        for p in predictions:
            print(f"  #{p.rank}: {p.label} ({p.percentage}) [raw: {p.raw_label}]")

if __name__ == "__main__":
    verify()
