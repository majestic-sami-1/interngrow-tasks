"""Tests for ImageClassifier and utility functions."""

from PIL import Image
import pytest
import torch

from src.classifier import ImageClassifier, format_class_name
from src.utils import create_confidence_chart


def test_format_class_name():
    assert format_class_name("golden_retriever") == "Golden Retriever"
    assert format_class_name("sports_car") == "Sports Car"
    assert format_class_name("coffee_mug") == "Coffee Mug"


def test_classifier_initialization():
    classifier = ImageClassifier(device="cpu")
    assert classifier.model is not None
    assert classifier.weights is not None
    assert len(classifier.categories) == 1000


def test_image_preprocessing():
    classifier = ImageClassifier(device="cpu")

    # Test RGB synthetic image
    rgb_img = Image.new("RGB", (300, 400), color=(120, 50, 200))
    tensor = classifier.preprocess(rgb_img)
    assert tensor.shape == (1, 3, 224, 224)
    assert isinstance(tensor, torch.Tensor)

    # Test RGBA image (with alpha channel)
    rgba_img = Image.new("RGBA", (150, 150), color=(255, 0, 0, 128))
    tensor_rgba = classifier.preprocess(rgba_img)
    assert tensor_rgba.shape == (1, 3, 224, 224)

    # Test Grayscale image
    gray_img = Image.new("L", (200, 200), color=128)
    tensor_gray = classifier.preprocess(gray_img)
    assert tensor_gray.shape == (1, 3, 224, 224)


def test_predict_top_k():
    classifier = ImageClassifier(device="cpu")
    test_img = Image.new("RGB", (256, 256), color=(200, 100, 50))

    # Test top_k = 3
    results, latency = classifier.predict(test_img, top_k=3)
    assert len(results) == 3
    assert latency > 0
    assert results[0].rank == 1
    assert 0.0 <= results[0].confidence <= 1.0

    # Test top_k = 5
    results_5, _ = classifier.predict(test_img, top_k=5)
    assert len(results_5) == 5
    # Ensure descending order of confidence
    for i in range(len(results_5) - 1):
        assert results_5[i].confidence >= results_5[i + 1].confidence


def test_create_confidence_chart():
    classifier = ImageClassifier(device="cpu")
    test_img = Image.new("RGB", (224, 224), color=(50, 150, 200))
    results, _ = classifier.predict(test_img, top_k=4)

    fig = create_confidence_chart(results)
    assert fig is not None
    assert len(fig.data) == 1
    assert len(fig.data[0].x) == 4
