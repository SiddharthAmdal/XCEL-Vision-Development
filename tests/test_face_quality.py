import pytest
import numpy as np
from ai.face.opencv_quality import OpenCVFaceQualityAnalyzer

@pytest.fixture
def analyzer():
    return OpenCVFaceQualityAnalyzer(min_width=40, min_height=40, min_blur=50.0, min_brightness=20.0)

def test_undersized_face(analyzer):
    img = np.ones((30, 30, 3), dtype=np.uint8) * 100
    quality = analyzer.analyze_quality(img)
    assert quality.width == 30
    assert quality.height == 30
    assert quality.meets_threshold is False

def test_low_brightness_face(analyzer):
    # Dark image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    quality = analyzer.analyze_quality(img)
    assert quality.brightness == 0
    assert quality.meets_threshold is False

def test_blurry_face(analyzer):
    # Solid color is technically perfectly blurry (0 variance)
    img = np.ones((100, 100, 3), dtype=np.uint8) * 128
    quality = analyzer.analyze_quality(img)
    assert quality.blur_score == 0.0
    assert quality.meets_threshold is False

def test_sharp_sufficient_face(analyzer):
    # Create an image with high variance
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    quality = analyzer.analyze_quality(img)
    assert quality.width == 100
    assert quality.height == 100
    assert quality.blur_score > 50.0
    assert quality.brightness > 20.0
    assert quality.meets_threshold is True
