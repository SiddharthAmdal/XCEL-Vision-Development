from typing import List, Tuple, Optional, Dict
from xsc_lib.xsc_lib_common.models.ai import FaceDetection, Detection

def calculate_iou(boxA: Tuple[int, int, int, int], boxB: Tuple[int, int, int, int]) -> float:
    """Calculates Intersection over Union for two bounding boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)

    if interArea == 0:
        return 0.0

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

class PersonFaceAssociator:
    """
    Associates face detections with person tracking IDs using spatial overlap.
    """
    
    def associate(self, persons: List[Detection], face_bboxes: List[Tuple]) -> List[Dict]:
        """
        Maps a list of face bounding boxes to the corresponding person track_id.
        
        Args:
            persons: List of tracked Detection objects (representing people).
            face_bboxes: List of (bounding_box, confidence, [landmarks]) for detected faces.
            
        Returns:
            A list of dicts with keys: 'bbox', 'confidence', 'track_id'.
            'track_id' will be None if the face does not associate with any person.
        """
        results = []
        
        for item in face_bboxes:
            face_bbox = item[0]
            face_conf = item[1]
            
            fx1, fy1, fx2, fy2 = face_bbox
            face_center_x = (fx1 + fx2) // 2
            face_center_y = (fy1 + fy2) // 2
            
            candidates = []
            
            for person in persons:
                px1, py1, px2, py2 = person.bounding_box
                
                # Check if face center falls inside the person bounding box
                if px1 <= face_center_x <= px2 and py1 <= face_center_y <= py2:
                    iou = calculate_iou((fx1, fy1, fx2, fy2), (px1, py1, px2, py2))
                    candidates.append((person.track_id, iou))
                    
            assigned_track_id = None
            if candidates:
                # Sort candidates by IoU descending to tie-break
                candidates.sort(key=lambda x: x[1], reverse=True)
                assigned_track_id = candidates[0][0]
                
            results.append({
                'bbox': face_bbox,
                'confidence': face_conf,
                'track_id': assigned_track_id
            })
            
        return results
