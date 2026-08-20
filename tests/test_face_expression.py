import pytest
import numpy as np
from ai.face.ferplus_expression import FERPlusExpressionAnalyzer
from ai.models import FacialExpression

@pytest.fixture
def analyzer():
    return FERPlusExpressionAnalyzer()

def test_analyze_empty_image(analyzer):
    img = np.array([])
    res = analyzer.analyze_expression(img)
    assert res is None

def test_analyze_valid_face(analyzer):
    # Dummy face image 64x64
    img = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    res = analyzer.analyze_expression(img)
    
    assert isinstance(res, FacialExpression)
    assert res.label in analyzer.LABELS
    assert 0.0 <= res.confidence <= 1.0

def test_model_missing():
    with pytest.raises(FileNotFoundError):
        FERPlusExpressionAnalyzer(model_path="invalid_path.onnx")
