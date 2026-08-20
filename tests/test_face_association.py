import pytest
from ai.face.association import PersonFaceAssociator
from ai.models import Detection

@pytest.fixture
def associator():
    return PersonFaceAssociator()

def test_face_inside_one_person(associator):
    persons = [
        Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(0, 0, 100, 100))
    ]
    face_bboxes = [((25, 25, 75, 75), 0.95)]
    
    results = associator.associate(persons, face_bboxes)
    assert len(results) == 1
    assert results[0]['track_id'] == 1

def test_face_with_no_matching_person(associator):
    persons = [
        Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(0, 0, 50, 50))
    ]
    # Face center is at (75, 75) which is outside person (0,0,50,50)
    face_bboxes = [((50, 50, 100, 100), 0.95)]
    
    results = associator.associate(persons, face_bboxes)
    assert len(results) == 1
    assert results[0]['track_id'] is None

def test_overlapping_person_boxes_tie_breaking(associator):
    persons = [
        Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(0, 0, 100, 100)),
        Detection(track_id=2, class_name="person", confidence=0.9, bounding_box=(20, 20, 100, 100))
    ]
    # Face is inside both, but overlaps track_id=2 much more (almost identical)
    face_bboxes = [((20, 20, 90, 90), 0.95)]
    
    results = associator.associate(persons, face_bboxes)
    assert len(results) == 1
    # Should tie-break to track_id 2 because IoU is higher
    assert results[0]['track_id'] == 2

def test_multiple_faces_multiple_persons(associator):
    persons = [
        Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(0, 0, 100, 100)),
        Detection(track_id=2, class_name="person", confidence=0.9, bounding_box=(200, 200, 300, 300))
    ]
    face_bboxes = [
        ((25, 25, 75, 75), 0.95),
        ((225, 225, 275, 275), 0.99)
    ]
    
    results = associator.associate(persons, face_bboxes)
    assert len(results) == 2
    assert results[0]['track_id'] == 1
    assert results[1]['track_id'] == 2
