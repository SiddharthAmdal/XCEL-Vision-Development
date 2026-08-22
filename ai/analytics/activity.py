import math
from datetime import datetime
from typing import List, Tuple, Dict
from ai.analytics.models import (
    SessionAnalyticsState, ActivityState, ProximityEvent, 
    MotionHeatmap, AnomalyObservation, BehavioralEvidence,
    AdvancedSceneAnalyticsResponse
)
import logging

logger = logging.getLogger(__name__)

class ActivityAnalyticsEngine:
    def __init__(self):
        # Configuration for Advanced Analytics
        self.loitering_duration_threshold = 15.0 # Seconds before considering loitering
        self.loitering_spatial_threshold = 50.0  # Max distance moved to be considered loitering
        
        self.proximity_distance_threshold = 80.0 # Pixels (e.g. 1.5 meters depending on scale)
        self.proximity_duration_threshold = 5.0  # Seconds of sustained proximity
        
        self.frame_width = 640.0
        self.frame_height = 480.0
        
        self.anomaly_activity_threshold = 100.0 # Threshold for grid cell intensity to trigger anomaly

    def _distance(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def _calculate_activities(self, state: SessionAnalyticsState, timestamp: datetime) -> List[ActivityState]:
        activities = []
        for track_id, track in state.active_tracks.items():
            duration = (timestamp - track.first_seen).total_seconds()
            
            # If not enough history, INSUFFICIENT_EVIDENCE
            if duration < 2.0:
                activities.append(ActivityState(
                    track_id=track_id,
                    state="INSUFFICIENT_EVIDENCE",
                    confidence=0.0,
                    evidence=[]
                ))
                continue
                
            # Calculate total spatial movement in the recent window
            # Take the bounding box of recent centroids
            if track.recent_centroids:
                xs = [c[1][0] for c in track.recent_centroids]
                ys = [c[1][1] for c in track.recent_centroids]
                max_spread = max(max(xs) - min(xs), max(ys) - min(ys))
            else:
                max_spread = 0.0

            evidence = [
                BehavioralEvidence(cue="duration_seconds", value=duration),
                BehavioralEvidence(cue="spatial_spread", value=max_spread)
            ]

            activity_state = "STATIONARY"
            confidence = 0.7
            
            if max_spread > self.loitering_spatial_threshold:
                activity_state = "MOVING"
                confidence = min(1.0, max_spread / 200.0)
            elif duration > self.loitering_duration_threshold:
                activity_state = "LOITERING"
                confidence = min(1.0, duration / (self.loitering_duration_threshold * 2))
            
            activities.append(ActivityState(
                track_id=track_id,
                state=activity_state,
                confidence=confidence,
                evidence=evidence
            ))
            
        return activities

    def _calculate_interactions(self, state: SessionAnalyticsState, timestamp: datetime) -> List[ProximityEvent]:
        interactions = []
        # Find pairs of tracks
        active_ids = list(state.active_tracks.keys())
        for i in range(len(active_ids)):
            for j in range(i + 1, len(active_ids)):
                id_a = active_ids[i]
                id_b = active_ids[j]
                track_a = state.active_tracks[id_a]
                track_b = state.active_tracks[id_b]
                
                # We need overlapping temporal history to check sustained proximity
                # For simplicity in this implementation, we check the current distance.
                # In a robust system, we would maintain a pairwise history state.
                if not track_a.current_centroid or not track_b.current_centroid:
                    continue
                    
                dist = self._distance(track_a.current_centroid, track_b.current_centroid)
                
                if dist < self.proximity_distance_threshold:
                    # Calculate overlapping duration (approximate using min duration of both)
                    dur_a = (timestamp - track_a.first_seen).total_seconds()
                    dur_b = (timestamp - track_b.first_seen).total_seconds()
                    overlap = min(dur_a, dur_b)
                    
                    prox_state = "PROXIMITY"
                    if overlap >= self.proximity_duration_threshold:
                        prox_state = "SUSTAINED_PROXIMITY"
                        
                    score = max(0.0, 1.0 - (dist / self.proximity_distance_threshold))
                    
                    interactions.append(ProximityEvent(
                        track_a=id_a,
                        track_b=id_b,
                        proximity_score=score,
                        duration_seconds=overlap,
                        state=prox_state
                    ))
        return interactions

    def _update_and_get_heatmap(self, state: SessionAnalyticsState, timestamp: datetime) -> MotionHeatmap:
        if not state.heatmap_cells:
            state.heatmap_cells = [[0.0 for _ in range(state.heatmap_grid_width)] for _ in range(state.heatmap_grid_height)]
            
        cell_w = self.frame_width / state.heatmap_grid_width
        cell_h = self.frame_height / state.heatmap_grid_height
        
        # Increment heatmap for all current centroids
        for track in state.active_tracks.values():
            if track.current_centroid:
                cx, cy = track.current_centroid
                grid_x = int(min(cx // cell_w, state.heatmap_grid_width - 1))
                grid_y = int(min(cy // cell_h, state.heatmap_grid_height - 1))
                
                # Add intensity, decay is not implemented here but could be
                state.heatmap_cells[grid_y][grid_x] += 1.0
                
        # Normalize for response (max intensity = 1.0)
        max_val = max((max(row) for row in state.heatmap_cells), default=1.0)
        if max_val == 0:
            max_val = 1.0
            
        normalized_cells = [[min(1.0, val / max_val) for val in row] for row in state.heatmap_cells]
        
        return MotionHeatmap(
            grid_width=state.heatmap_grid_width,
            grid_height=state.heatmap_grid_height,
            cells=normalized_cells
        )

    def _calculate_anomalies(self, state: SessionAnalyticsState, heatmap: MotionHeatmap) -> List[AnomalyObservation]:
        # Lightweight statistical anomaly detection based on motion concentration
        anomalies = []
        
        # If any single cell has an extreme absolute value, flag it
        # The true absolute values are in state.heatmap_cells
        max_absolute = 0.0
        for row in state.heatmap_cells:
            max_absolute = max(max_absolute, max(row))
            
        if max_absolute > self.anomaly_activity_threshold:
            # We have a hot spot! 
            # Could indicate a crowded area or a stalled object creating false tracks
            anomalies.append(AnomalyObservation(
                type="MOTION_ANOMALY",
                score=min(1.0, max_absolute / (self.anomaly_activity_threshold * 2)),
                confidence=0.85,
                evidence=[
                    BehavioralEvidence(cue="spatial_activity_deviation", value=max_absolute)
                ]
            ))
            
        return anomalies

    def process_advanced_analytics(self, state: SessionAnalyticsState, timestamp: datetime) -> AdvancedSceneAnalyticsResponse:
        activities = self._calculate_activities(state, timestamp)
        interactions = self._calculate_interactions(state, timestamp)
        heatmap = self._update_and_get_heatmap(state, timestamp)
        anomalies = self._calculate_anomalies(state, heatmap)
        
        return AdvancedSceneAnalyticsResponse(
            camera_id=state.camera_id,
            session_id=state.session_id,
            timestamp=timestamp,
            activities=activities,
            interactions=interactions,
            heatmap=heatmap,
            anomalies=anomalies
        )
