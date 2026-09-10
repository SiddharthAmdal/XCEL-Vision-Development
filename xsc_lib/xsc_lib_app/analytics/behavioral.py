import math
from datetime import datetime, timezone
from typing import List, Dict, Tuple
from xsc_lib.xsc_lib_common.models.analytics import TrackHistory, BehavioralTemporalConfig, AffectiveIndicator, BehavioralEvidence
import logging

logger = logging.getLogger(__name__)

class BehavioralEngine:
    def __init__(self, config: BehavioralTemporalConfig = None):
        self.config = config or BehavioralTemporalConfig()

    def prune_buffers(self, track: TrackHistory, current_time: datetime):
        """Remove observations older than window_seconds."""
        cutoff_time = current_time.timestamp() - self.config.window_seconds
        
        track.recent_centroids = [
            obs for obs in track.recent_centroids 
            if obs[0].timestamp() >= cutoff_time
        ][-self.config.max_observations:]
        
        track.recent_expressions = [
            obs for obs in track.recent_expressions 
            if obs[0].timestamp() >= cutoff_time
        ][-self.config.max_observations:]
        
        track.recent_face_visibility = [
            obs for obs in track.recent_face_visibility 
            if obs[0].timestamp() >= cutoff_time
        ][-self.config.max_observations:]

    def _calculate_distance(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def extract_cues(self, track: TrackHistory) -> Dict[str, float]:
        """Extract observable behavioral cues from the temporal buffers."""
        cues = {
            "movement_velocity": 0.0,
            "movement_variability": 0.0,
            "direction_change_frequency": 0.0,
            "time_stationary": 0.0,
            "expression_volatility": 0.0,
            "expression_persistence": 0.0,
            "tracking_stability": 0.0,
            "face_visibility_ratio": 0.0,
            "fear_surprise_frequency": 0.0,
            "neutral_happy_frequency": 0.0
        }

        # 1. Tracking & Face Visibility Cues
        num_centroids = len(track.recent_centroids)
        if num_centroids > 0:
            cues["tracking_stability"] = min(1.0, num_centroids / (self.config.window_seconds * 2.5)) # Approximate against 2.5 FPS expected minimum
            
        num_vis = len(track.recent_face_visibility)
        if num_vis > 0:
            visible_count = sum(1 for v in track.recent_face_visibility if v[1])
            cues["face_visibility_ratio"] = visible_count / num_vis

        # 2. Movement Cues
        if num_centroids >= 2:
            distances = []
            vectors = []
            stationary_frames = 0
            
            for i in range(1, num_centroids):
                t1, p1 = track.recent_centroids[i-1]
                t2, p2 = track.recent_centroids[i]
                
                dist = self._calculate_distance(p1, p2)
                distances.append(dist)
                
                if dist < 5.0: # 5 pixels threshold for stationary
                    stationary_frames += 1
                
                # Direction vector
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                
                if dist > 0:
                    vectors.append((dx/dist, dy/dist))
                    
            # Velocity (pixels per second in the buffer)
            time_span = (track.recent_centroids[-1][0] - track.recent_centroids[0][0]).total_seconds()
            if time_span > 0:
                total_dist = sum(distances)
                cues["movement_velocity"] = total_dist / time_span
                cues["time_stationary"] = stationary_frames * (time_span / num_centroids)
            
            # Variability (Standard deviation of distances)
            if len(distances) > 1:
                mean_dist = sum(distances) / len(distances)
                var = sum((d - mean_dist)**2 for d in distances) / len(distances)
                cues["movement_variability"] = math.sqrt(var)

            # Direction changes (dot product of consecutive normalized vectors)
            dir_changes = 0
            for i in range(1, len(vectors)):
                v1 = vectors[i-1]
                v2 = vectors[i]
                dot = v1[0]*v2[0] + v1[1]*v2[1]
                # dot < 0.5 means > 60 degree change
                if dot < 0.5:
                    dir_changes += 1
            if time_span > 0:
                cues["direction_change_frequency"] = dir_changes / time_span

        # 3. Expression Cues
        num_expr = len(track.recent_expressions)
        if num_expr > 0:
            expr_changes = 0
            fear_surprise = 0
            neutral_happy = 0
            
            for i in range(num_expr):
                _, label = track.recent_expressions[i]
                
                if label in ["fear", "surprise"]:
                    fear_surprise += 1
                if label in ["neutral", "happiness"]:
                    neutral_happy += 1
                    
                if i > 0:
                    prev_label = track.recent_expressions[i-1][1]
                    if prev_label != label:
                        expr_changes += 1
                        
            time_span = (track.recent_expressions[-1][0] - track.recent_expressions[0][0]).total_seconds()
            if time_span > 0:
                cues["expression_volatility"] = expr_changes / time_span
                
            cues["expression_persistence"] = 1.0 - (expr_changes / max(1, num_expr))
            cues["fear_surprise_frequency"] = fear_surprise / num_expr
            cues["neutral_happy_frequency"] = neutral_happy / num_expr

        return cues

    def _normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp and normalize a value between 0 and 1."""
        if value <= min_val:
            return 0.0
        if value >= max_val:
            return 1.0
        return (value - min_val) / (max_val - min_val)

    def infer_indicators(self, track: TrackHistory, cues: Dict[str, float]) -> List[AffectiveIndicator]:
        """Map behavioral cues to affective indicators with evidence."""
        indicators = []
        
        # Check sufficient evidence (need at least 2 seconds of tracking)
        time_tracked = 0
        if track.recent_centroids:
            time_tracked = (track.recent_centroids[-1][0] - track.recent_centroids[0][0]).total_seconds()
            
        if time_tracked < 2.0 or cues["tracking_stability"] < 0.3:
            # Return insufficient evidence state for all
            insufficient = AffectiveIndicator(
                state="insufficient_evidence", score=0.0, confidence=0.0,
                evidence=[BehavioralEvidence(cue="tracking_duration", value=time_tracked)]
            )
            return [insufficient]

        # General confidence penalty for lack of face visibility
        face_confidence = cues["face_visibility_ratio"]

        # --- NERVOUSNESS ---
        # High movement variability + Frequent direction changes + High expression volatility + Fear/Surprise
        n_vel = self._normalize_score(cues["movement_velocity"], 100, 300)
        n_var = self._normalize_score(cues["movement_variability"], 5, 20)
        n_dir = self._normalize_score(cues["direction_change_frequency"], 0.5, 3.0)
        n_vol = self._normalize_score(cues["expression_volatility"], 0.2, 1.5)
        n_fs = cues["fear_surprise_frequency"]
        
        nervous_score = (n_var * 0.3) + (n_dir * 0.3) + (n_vol * 0.2) + (n_fs * 0.2)
        nervous_conf = 0.5 + (face_confidence * 0.5) # Minimum confidence if track is good
        
        indicators.append(AffectiveIndicator(
            state="nervousness",
            score=min(1.0, nervous_score),
            confidence=nervous_conf,
            evidence=[
                BehavioralEvidence(cue="movement_variability", value=n_var),
                BehavioralEvidence(cue="direction_change_frequency", value=n_dir),
                BehavioralEvidence(cue="expression_volatility", value=n_vol),
                BehavioralEvidence(cue="fear_surprise_frequency", value=n_fs)
            ]
        ))

        # --- ENGAGEMENT ---
        # Sustained face visibility + tracking stability + expression persistence + temporal presence
        e_vis = cues["face_visibility_ratio"]
        e_per = cues["expression_persistence"]
        e_time = self._normalize_score(time_tracked, 2.0, 5.0)
        
        engage_score = (e_vis * 0.5) + (e_per * 0.3) + (e_time * 0.2)
        engage_conf = face_confidence # Requires face for true engagement
        
        indicators.append(AffectiveIndicator(
            state="engagement",
            score=min(1.0, engage_score),
            confidence=engage_conf,
            evidence=[
                BehavioralEvidence(cue="face_visibility_ratio", value=e_vis),
                BehavioralEvidence(cue="expression_persistence", value=e_per),
                BehavioralEvidence(cue="temporal_presence", value=e_time)
            ]
        ))

        # --- CALMNESS ---
        # Low velocity + Low variability + High stationary + Neutral/Happy expressions
        c_vel = 1.0 - self._normalize_score(cues["movement_velocity"], 50, 200)
        c_var = 1.0 - self._normalize_score(cues["movement_variability"], 5, 20)
        c_stat = self._normalize_score(cues["time_stationary"], 1.0, 4.0)
        c_nh = cues["neutral_happy_frequency"]
        
        calm_score = (c_vel * 0.2) + (c_var * 0.2) + (c_stat * 0.4) + (c_nh * 0.2)
        calm_conf = 0.6 + (face_confidence * 0.4)
        
        indicators.append(AffectiveIndicator(
            state="calmness",
            score=min(1.0, calm_score),
            confidence=calm_conf,
            evidence=[
                BehavioralEvidence(cue="low_velocity", value=c_vel),
                BehavioralEvidence(cue="time_stationary", value=c_stat),
                BehavioralEvidence(cue="neutral_happy_frequency", value=c_nh)
            ]
        ))

        # --- CONFIDENCE/SELF-ASSURANCE ---
        # Stable tracking + low hesitation (low dir changes) + sustained presence
        s_dir = 1.0 - self._normalize_score(cues["direction_change_frequency"], 0.2, 1.5)
        s_stat = self._normalize_score(cues["time_stationary"], 0.5, 2.0)
        
        conf_score = (s_dir * 0.4) + (s_stat * 0.3) + (e_time * 0.3)
        conf_conf = 0.5 + (face_confidence * 0.5)
        
        indicators.append(AffectiveIndicator(
            state="confidence_indicator",
            score=min(1.0, conf_score),
            confidence=conf_conf,
            evidence=[
                BehavioralEvidence(cue="low_direction_changes", value=s_dir),
                BehavioralEvidence(cue="movement_stability", value=s_stat),
                BehavioralEvidence(cue="temporal_presence", value=e_time)
            ]
        ))

        return indicators

    def process_track(self, track: TrackHistory, current_time: datetime):
        """Orchestrator for updating a track's behavioral state."""
        self.prune_buffers(track, current_time)
        cues = self.extract_cues(track)
        indicators = self.infer_indicators(track, cues)
        track.affective_indicators = indicators
