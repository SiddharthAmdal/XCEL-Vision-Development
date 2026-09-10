import math
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Optional
from xsc_lib.xsc_lib_common.models.ai import Detection
from xsc_lib.xsc_lib_common.models.analytics import (
    CountingLine, TrackHistory, SessionAnalyticsState,
    EntryEvent, ExitEvent, OccupancyResponse, PeopleAnalyticsResponse, PersonAnalytics, DwellAnalyticsResponse,
    BehavioralTemporalConfig
)
from xsc_lib.xsc_lib_app.analytics.behavioral import BehavioralEngine
from xsc_lib.xsc_lib_app.analytics.activity import ActivityAnalyticsEngine
import logging

logger = logging.getLogger(__name__)

def ccw(A: Tuple[int, int], B: Tuple[int, int], C: Tuple[int, int]) -> bool:
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def intersect(A: Tuple[int, int], B: Tuple[int, int], C: Tuple[int, int], D: Tuple[int, int]) -> bool:
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

def get_side(L1: Tuple[int, int], L2: Tuple[int, int], P: Tuple[int, int]) -> float:
    # Cross product to determine side of the line
    return (L2[0] - L1[0]) * (P[1] - L1[1]) - (L2[1] - L1[1]) * (P[0] - L1[0])

class SessionAnalyticsEngine:
    def __init__(self):
        self._sessions: Dict[str, SessionAnalyticsState] = {}
        # For debounce distance
        self.debounce_distance = 40.0
        self.behavioral_engine = BehavioralEngine()
        self.activity_engine = ActivityAnalyticsEngine()

    def _get_session_key(self, camera_id: str, session_id: str) -> str:
        return f"{camera_id}_{session_id}"

    def initialize_session(self, camera_id: str, session_id: str, lines: List[CountingLine] = None, initial_occupancy: int = 0):
        key = self._get_session_key(camera_id, session_id)
        if key not in self._sessions:
            logger.info(f"Initializing analytics state for {key}")
            self._sessions[key] = SessionAnalyticsState(
                camera_id=camera_id,
                session_id=session_id,
                initial_occupancy=initial_occupancy,
                estimated_occupancy=initial_occupancy,
                lines=lines or []
            )

    def cleanup_session(self, camera_id: str, session_id: str):
        key = self._get_session_key(camera_id, session_id)
        if key in self._sessions:
            logger.info(f"Destroying analytics state for {key}")
            del self._sessions[key]

    def get_state(self, camera_id: str, session_id: str) -> Optional[SessionAnalyticsState]:
        key = self._get_session_key(camera_id, session_id)
        return self._sessions.get(key)
        
    def _calculate_centroid(self, bbox: Tuple[int, int, int, int]) -> Tuple[int, int]:
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def _distance(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def process_detections(self, camera_id: str, session_id: str, detections: List[Detection], faces: List, timestamp: datetime) -> SessionAnalyticsState:
        # Auto-initialize with a default line if not exists (for testing/MVP)
        key = self._get_session_key(camera_id, session_id)
        if key not in self._sessions:
            default_line = CountingLine(
                id="default_vertical_line",
                start_point=(320, 0),
                end_point=(320, 480), # Assuming 640x480 generic center line
                direction="left_to_right" # Crossing from left (x < 320) to right (x > 320) is ENTRY
            )
            self.initialize_session(camera_id, session_id, lines=[default_line])
            
        state = self._sessions[key]
        
        current_track_ids = set()
        
        # 1. Update active tracks
        for det in detections:
            track_id = det.track_id
            current_track_ids.add(track_id)
            centroid = self._calculate_centroid(det.bounding_box)
            
            if track_id not in state.active_tracks:
                state.active_tracks[track_id] = TrackHistory(
                    track_id=track_id,
                    first_seen=timestamp,
                    last_seen=timestamp,
                    current_centroid=centroid,
                    recent_centroids=[(timestamp, centroid)]
                )
            else:
                track = state.active_tracks[track_id]
                track.previous_centroid = track.current_centroid
                track.current_centroid = centroid
                track.last_seen = timestamp
                track.total_visible_duration = (timestamp - track.first_seen).total_seconds()
                track.recent_centroids.append((timestamp, centroid))
                
                # 2. Check Line Crossing
                if track.previous_centroid and track.current_centroid:
                    for line in state.lines:
                        if not line.enabled:
                            continue
                            
                        # If in debounce, check if moved far enough away to clear
                        if track.crossing_debounce_state:
                            dist_to_line_start = self._distance(track.current_centroid, line.start_point)
                            dist_to_line_end = self._distance(track.current_centroid, line.end_point)
                            # Approximate distance to segment, but simple point distance is okay for MVP debounce
                            # Alternatively just wait N seconds, but spatial debounce is better.
                            dist_prev_to_curr = self._distance(track.previous_centroid, track.current_centroid)
                            # Actually, if we just check if it moved 40 pixels away from the crossing point.
                            # For simplicity, we just clear debounce if they are on one side and far enough.
                        if track.crossing_debounce_state:
                            pass # We will handle debounce dynamically by checking if it crosses again
                        
                        if intersect(track.previous_centroid, track.current_centroid, line.start_point, line.end_point):
                            # It crossed. Determine direction.
                            # We compare X coordinates for a vertical line. 
                            # More generally, we can use the sign of get_side.
                            side_prev = get_side(line.start_point, line.end_point, track.previous_centroid)
                            side_curr = get_side(line.start_point, line.end_point, track.current_centroid)
                            
                            is_entry = False
                            is_exit = False
                            
                            if line.direction == "left_to_right":
                                if track.previous_centroid[0] < line.start_point[0] and track.current_centroid[0] >= line.start_point[0]:
                                    is_entry = True
                                elif track.previous_centroid[0] > line.start_point[0] and track.current_centroid[0] <= line.start_point[0]:
                                    is_exit = True
                            
                            if is_entry and track.last_crossing_state != "ENTRY":
                                state.entries += 1
                                state.estimated_occupancy += 1
                                state.entry_events.append(EntryEvent(
                                    camera_id=camera_id, session_id=session_id, track_id=track_id, timestamp=timestamp, line_id=line.id
                                ))
                                track.last_crossing_state = "ENTRY"
                                track.entry_timestamp = timestamp
                                track.crossing_debounce_state = True
                                logger.info(f"Session {session_id}: Track {track_id} triggered ENTRY.")
                                
                            elif is_exit and track.last_crossing_state != "EXIT":
                                state.exits += 1
                                state.estimated_occupancy -= 1
                                state.exit_events.append(ExitEvent(
                                    camera_id=camera_id, session_id=session_id, track_id=track_id, timestamp=timestamp, line_id=line.id
                                ))
                                track.last_crossing_state = "EXIT"
                                track.exit_timestamp = timestamp
                                track.crossing_debounce_state = True
                                logger.info(f"Session {session_id}: Track {track_id} triggered EXIT.")

        # 2.5 Update Behavioral Data and Execute Behavioral Engine
        face_map = {f.track_id: f for f in faces if f.track_id is not None}
        for track_id, track in state.active_tracks.items():
            if track_id in current_track_ids:
                face = face_map.get(track_id)
                if face:
                    track.recent_face_visibility.append((timestamp, True))
                    if face.expression:
                        track.recent_expressions.append((timestamp, face.expression.label))
                else:
                    track.recent_face_visibility.append((timestamp, False))
            
            # Execute pruning, cue extraction, and scoring for active tracks
            self.behavioral_engine.process_track(track, timestamp)

        # Update heatmap every frame via ActivityEngine
        self.activity_engine._update_and_get_heatmap(state, timestamp)

        # 3. Clean up lost tracks
        # ByteTrack handles temporary loss (track_buffer), so if it's completely gone from detections, 
        # it might just be occluded. For analytics, we keep it in active_tracks until a timeout or just 
        # keep it forever in session state until session ends. 
        # To avoid unbounded memory in long sessions, we can reap tracks not seen for 5 minutes.
        tracks_to_delete = []
        for tid, track in state.active_tracks.items():
            if tid not in current_track_ids:
                time_since_last_seen = (timestamp - track.last_seen).total_seconds()
                if time_since_last_seen > 300: # 5 minutes
                    tracks_to_delete.append(tid)
                    
        for tid in tracks_to_delete:
            del state.active_tracks[tid]
            
        state.visible_people = len(current_track_ids)
        return state

    def get_occupancy(self, camera_id: str, session_id: str) -> OccupancyResponse:
        state = self.get_state(camera_id, session_id)
        if not state:
            return OccupancyResponse(
                camera_id=camera_id, visible_people=0, initial_occupancy=0,
                total_entries=0, total_exits=0, estimated_occupancy=0, timestamp=datetime.utcnow()
            )
        return OccupancyResponse(
            camera_id=camera_id,
            visible_people=state.visible_people,
            initial_occupancy=state.initial_occupancy,
            total_entries=state.entries,
            total_exits=state.exits,
            estimated_occupancy=state.estimated_occupancy,
            timestamp=datetime.utcnow()
        )

    def get_people(self, camera_id: str, session_id: str) -> PeopleAnalyticsResponse:
        state = self.get_state(camera_id, session_id)
        people = []
        if state:
            for track in state.active_tracks.values():
                people.append(PersonAnalytics(
                    track_id=track.track_id,
                    first_seen=track.first_seen,
                    last_seen=track.last_seen,
                    dwell_time_seconds=track.total_visible_duration
                ))
        return PeopleAnalyticsResponse(
            camera_id=camera_id, timestamp=datetime.utcnow(), people=people
        )

    def get_dwell(self, camera_id: str, session_id: str) -> DwellAnalyticsResponse:
        state = self.get_state(camera_id, session_id)
        avg_dwell = 0.0
        count = 0
        if state and state.active_tracks:
            total_dwell = sum(t.total_visible_duration for t in state.active_tracks.values())
            count = len(state.active_tracks)
            avg_dwell = total_dwell / count if count > 0 else 0.0
            
        return DwellAnalyticsResponse(
            camera_id=camera_id, timestamp=datetime.utcnow(),
            average_dwell_time_seconds=avg_dwell, active_tracks_count=count
        )
