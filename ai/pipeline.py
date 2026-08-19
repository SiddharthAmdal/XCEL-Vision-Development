import cv2
from datetime import datetime
from typing import Iterator
from ultralytics import YOLO
from ai.models import AIFrameResult, Detection
import logging

logger = logging.getLogger(__name__)

class VideoAIPipeline:
    def __init__(self, target_fps: int = 5):
        # Load YOLOv8 nano model
        self.model = YOLO("yolov8n.pt")
        self.target_fps = target_fps

    def process_video(self, camera_id: str, video_path: str) -> Iterator[AIFrameResult]:
        """
        Processes a recorded MP4 video through the AI pipeline.
        Yields AIFrameResult objects containing detection and tracking data.
        """
        logger.info(f"Starting AI pipeline for camera {camera_id} on file {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video file: {video_path}")
            raise ValueError(f"Cannot open video file: {video_path}")
            
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        if original_fps <= 0:
            original_fps = 30
            
        frame_skip = int(original_fps / self.target_fps) if self.target_fps > 0 else 1
        frame_skip = max(1, frame_skip)
        
        frame_idx = 0
        base_timestamp = datetime.utcnow()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_idx % frame_skip == 0:
                # Run YOLO tracking with built-in ByteTrack configuration
                # classes=[0] filters for 'person' class only
                results = self.model.track(frame, persist=True, tracker="bytetrack.yaml", classes=[0], verbose=False)
                
                detections = []
                for result in results:
                    boxes = result.boxes
                    if boxes is not None and boxes.id is not None:
                        for box, track_id, conf in zip(boxes.xyxy, boxes.id, boxes.conf):
                            x1, y1, x2, y2 = box.tolist()
                            detections.append(Detection(
                                track_id=int(track_id.item()),
                                class_name="person",
                                confidence=float(conf.item()),
                                bounding_box=(int(x1), int(y1), int(x2), int(y2))
                            ))
                
                yield AIFrameResult(
                    camera_id=camera_id,
                    timestamp=base_timestamp,
                    frame_number=frame_idx,
                    persons=len(detections),
                    detections=detections
                )
                
            frame_idx += 1
            
        cap.release()
        logger.info(f"Finished AI pipeline for camera {camera_id}")
