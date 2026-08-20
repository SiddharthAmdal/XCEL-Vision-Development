from pydantic import BaseModel, Field
from typing import Optional, List, Tuple
from datetime import datetime

class CountingLine(BaseModel):
    id: str
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]
    direction: str  # "left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top"
    enabled: bool = True

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
