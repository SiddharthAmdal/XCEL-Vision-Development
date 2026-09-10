from pydantic import BaseModel, Field
from typing import Optional, List, Tuple
from datetime import datetime

class CountingLine(BaseModel):
    id: str
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]
    direction: str  # "left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top"
    enabled: bool = True

class BehavioralTemporalConfig(BaseModel):
    window_seconds: float = 5.0
    max_observations: int = 150 # Upper bound

class BehavioralEvidence(BaseModel):
    cue: str
    value: float

class AffectiveIndicator(BaseModel):
    state: str
    score: float
    confidence: float
    evidence: List[BehavioralEvidence]

class TrackHistory(BaseModel):
    track_id: int
    first_seen: datetime
    last_seen: datetime
    previous_centroid: Optional[Tuple[int, int]] = None
    current_centroid: Optional[Tuple[int, int]] = None
    total_visible_duration: float = 0.0
    last_crossing_state: Optional[str] = None # "ENTRY", "EXIT", or None
    entry_timestamp: Optional[datetime] = None
    exit_timestamp: Optional[datetime] = None
    crossing_debounce_state: bool = False
    
    # Phase 8 Behavioral Temporal Buffers
    recent_centroids: List[Tuple[datetime, Tuple[int, int]]] = Field(default_factory=list)
    recent_expressions: List[Tuple[datetime, str]] = Field(default_factory=list)
    recent_face_visibility: List[Tuple[datetime, bool]] = Field(default_factory=list)
    
    affective_indicators: List[AffectiveIndicator] = Field(default_factory=list)

class EntryEvent(BaseModel):
    camera_id: str
    session_id: str
    track_id: int
    timestamp: datetime
    line_id: str

class ExitEvent(BaseModel):
    camera_id: str
    session_id: str
    track_id: int
    timestamp: datetime
    line_id: str

class SessionAnalyticsState(BaseModel):
    camera_id: str
    session_id: str
    active_tracks: dict[int, TrackHistory] = Field(default_factory=dict)
    visible_people: int = 0
    estimated_occupancy: int = 0
    initial_occupancy: int = 0
    entries: int = 0
    exits: int = 0
    entry_events: List[EntryEvent] = Field(default_factory=list)
    exit_events: List[ExitEvent] = Field(default_factory=list)
    lines: List[CountingLine] = Field(default_factory=list)
    heatmap_cells: List[List[float]] = Field(default_factory=list)
    heatmap_grid_width: int = 16
    heatmap_grid_height: int = 12
    anomaly_observations: List['AnomalyObservation'] = Field(default_factory=list)
    
class OccupancyResponse(BaseModel):
    camera_id: str
    visible_people: int
    initial_occupancy: int
    total_entries: int
    total_exits: int
    estimated_occupancy: int
    timestamp: datetime

class PersonAnalytics(BaseModel):
    track_id: int
    first_seen: datetime
    last_seen: datetime
    dwell_time_seconds: float
    
class PeopleAnalyticsResponse(BaseModel):
    camera_id: str
    timestamp: datetime
    people: List[PersonAnalytics]

class DwellAnalyticsResponse(BaseModel):
    camera_id: str
    timestamp: datetime
    average_dwell_time_seconds: float
    active_tracks_count: int

class TrackBehavior(BaseModel):
    track_id: int
    indicators: List[AffectiveIndicator]
    is_active: bool = True

class BehavioralResponse(BaseModel):
    camera_id: str
    session_id: str
    timestamp: datetime
    tracks: List[TrackBehavior]

# --- Phase 9 Models ---

class ActivityState(BaseModel):
    track_id: int
    state: str  # e.g., "MOVING", "STATIONARY", "LOITERING"
    confidence: float
    evidence: List[BehavioralEvidence] = Field(default_factory=list)

class ProximityEvent(BaseModel):
    track_a: int
    track_b: int
    proximity_score: float
    duration_seconds: float
    state: str # e.g., "PROXIMITY", "SUSTAINED_PROXIMITY"

class MotionHeatmap(BaseModel):
    grid_width: int
    grid_height: int
    cells: List[List[float]] # 2D array of normalized intensity values [0.0 - 1.0]

class AnomalyObservation(BaseModel):
    type: str # e.g., "MOTION_ANOMALY"
    score: float
    confidence: float
    evidence: List[BehavioralEvidence] = Field(default_factory=list)

class AdvancedSceneAnalyticsResponse(BaseModel):
    camera_id: str
    session_id: str
    timestamp: datetime
    activities: List[ActivityState] = Field(default_factory=list)
    interactions: List[ProximityEvent] = Field(default_factory=list)
    heatmap: Optional[MotionHeatmap] = None
    anomalies: List[AnomalyObservation] = Field(default_factory=list)
