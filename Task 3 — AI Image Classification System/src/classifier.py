"""Image classification module using pre-trained MobileNetV2."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, List, Optional
from PIL import Image
import torch
import torchvision.transforms as transforms
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2


def format_class_name(raw_name: str) -> str:
    """Format ImageNet class name into a clean, human-readable string.

    Examples:
        'golden_retriever' -> 'Golden Retriever'
        'tiger_shark' -> 'Tiger Shark'
    """
    cleaned = raw_name.replace("_", " ").strip()
    return cleaned.title()


@dataclass
class PredictionResult:
    """Structured representation of a single classification prediction."""

    rank: int
    raw_label: str
    label: str
    confidence: float
    percentage: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "raw_label": self.raw_label,
            "label": self.label,
            "confidence": self.confidence,
            "percentage": self.percentage,
        }


class ImageClassifier:
    """Wrapper around MobileNetV2 for PyTorch ImageNet classification."""

    def __init__(self, device: Optional[str] = None):
        """Initialize the classifier and load MobileNetV2 weights.

        Args:
            device: Computing device ('cpu' or 'cuda'). Auto-detected if None.
        """
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Load MobileNetV2 pre-trained on ImageNet-1k
        self.weights = MobileNet_V2_Weights.DEFAULT
        self.model = mobilenet_v2(weights=self.weights)
        self.model.to(self.device)
        self.model.eval()

        # Categories from ImageNet metadata
        self.categories = self.weights.meta.get("categories", [])

        # Standard canonical preprocessing transforms
        self.transform = transforms.Compose(
            [
                transforms.Resize(256, interpolation=transforms.InterpolationMode.BILINEAR),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """Preprocess a PIL image into a normalized tensor ready for model input.

        Args:
            image: Input PIL Image (any mode).

        Returns:
            Preprocessed 4D tensor with shape [1, 3, 224, 224].
        """
        # Ensure image is in RGB mode
        if image.mode != "RGB":
            image = image.convert("RGB")

        tensor = self.transform(image)
        # Add batch dimension: [3, 224, 224] -> [1, 3, 224, 224]
        tensor_batch = tensor.unsqueeze(0).to(self.device)
        return tensor_batch

    def predict(
        self, image: Image.Image, top_k: int = 5
    ) -> tuple[List[PredictionResult], float]:
        """Run classification inference on an input image.

        Args:
            image: PIL Image to classify.
            top_k: Number of top predictions to return (between 1 and 1000).

        Returns:
            Tuple of (list of PredictionResult objects, latency in milliseconds).
        """
        top_k = max(1, min(top_k, len(self.categories)))
        tensor_batch = self.preprocess(image)

        start_time = time.perf_counter()
        with torch.no_grad():
            outputs = self.model(tensor_batch)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            top_probs, top_indices = torch.topk(probabilities, top_k)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        results: List[PredictionResult] = []
        for rank, (prob, idx) in enumerate(zip(top_probs, top_indices), start=1):
            idx_int = idx.item()
            raw_label = (
                self.categories[idx_int]
                if idx_int < len(self.categories)
                else f"Class #{idx_int}"
            )
            confidence_val = float(prob.item())
            results.append(
                PredictionResult(
                    rank=rank,
                    raw_label=raw_label,
                    label=format_class_name(raw_label),
                    confidence=confidence_val,
                    percentage=f"{confidence_val * 100.0:.2f}%",
                )
            )

        return results, latency_ms


# Module-level cached instance helper
_classifier_instance: Optional[ImageClassifier] = None


def get_classifier() -> ImageClassifier:
    """Get or instantiate the global singleton classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = ImageClassifier()
    return _classifier_instance
