import React from 'react';

export interface AnalyticsData {
  visible_people: number;
  initial_occupancy: number;
  total_entries: number;
  total_exits: number;
  estimated_occupancy: number;
  average_dwell_time_seconds: number;
}

export interface BehavioralEvidence {
  cue: string;
  value: number;
}

export interface AffectiveIndicator {
  state: string;
  score: number;
  confidence: number;
  evidence: BehavioralEvidence[];
}

export interface TrackBehavior {
  track_id: number;
  indicators: AffectiveIndicator[];
  is_active?: boolean;
}

export interface BehavioralData {
  tracks: TrackBehavior[];
}

export interface ActivityState {
  track_id: number;
  state: string;
  confidence: number;
}

export interface ProximityEvent {
  track_a: number;
  track_b: number;
  duration_seconds: number;
  state: string;
}

export interface MotionHeatmap {
  grid_width: int;
  grid_height: int;
  cells: number[][];
}

export interface AnomalyObservation {
  type: string;
  score: number;
  confidence: number;
}

export interface SceneAnalyticsData {
  activities: ActivityState[];
  interactions: ProximityEvent[];
  heatmap: MotionHeatmap | null;
  anomalies: AnomalyObservation[];
}

interface AnalyticsDisplayProps {
  data: AnalyticsData | null;
  behavior?: BehavioralData | null;
  scene?: SceneAnalyticsData | null;
}

export const AnalyticsDisplay: React.FC<AnalyticsDisplayProps> = ({ data, behavior, scene }) => {
  if (!data) return null;
  
  // Filter active tracks and assign a generic "Person X" label mapping based on order
  const activeTracks = behavior?.tracks.filter(t => t.is_active !== false) || [];
  
  return (
    <div style={{
      background: 'var(--surface-light)',
      borderRadius: '12px',
      padding: '24px',
      color: 'var(--text-primary)',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      marginTop: '24px'
    }}>
      <h3 style={{ margin: '0 0 20px 0', fontSize: '20px', fontWeight: 'bold' }}>
        Session Analytics
      </h3>
      
      <div style={{ marginBottom: '32px' }}>
        <h4 style={{ margin: '0 0 16px 0', fontSize: '14px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Session Overview
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '16px' }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '16px', borderRadius: '8px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Visible People</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{data.visible_people}</div>
          </div>
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '16px', borderRadius: '8px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Occupancy</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--primary-color)' }}>{data.estimated_occupancy}</div>
          </div>
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '16px', borderRadius: '8px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Entries</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--success-color)' }}>{data.total_entries}</div>
          </div>
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '16px', borderRadius: '8px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Exits</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--danger-color)' }}>{data.total_exits}</div>
          </div>
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '16px', borderRadius: '8px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Avg Dwell Time</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{data.average_dwell_time_seconds.toFixed(1)}s</div>
          </div>
        </div>
      </div>

      {activeTracks.length > 0 && (
        <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '24px' }}>
          <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Behavioral Indicators
          </h4>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '20px', fontStyle: 'italic' }}>
            AI-derived behavioral indicators based on observable visual patterns. Not a psychological diagnosis.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
            {activeTracks.map((track, index) => (
              <div key={track.track_id} style={{ background: 'var(--surface-dark)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <div style={{ marginBottom: '16px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', paddingBottom: '12px' }}>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#fff' }}>Person {index + 1}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Track ID: {track.track_id}</div>
                </div>
                
                {track.indicators.map((indicator, idx) => {
                  if (indicator.state === "insufficient_evidence") {
                    return (
                      <div key={idx} style={{ fontSize: '13px', color: 'var(--text-secondary)', padding: '12px 0' }}>
                        Gathering evidence...
                      </div>
                    );
                  }
                  
                  const formatLabel = (str: string) => str.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                  
                  return (
                    <div key={idx} style={{ marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                        <span style={{ fontSize: '14px', color: '#cbd5e1' }}>{formatLabel(indicator.state)}</span>
                        <span style={{ fontSize: '16px', fontWeight: 'bold', color: indicator.score > 0.5 ? 'var(--success-color)' : '#fff' }}>
                          {Math.round(indicator.score * 100)}%
                        </span>
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                        Confidence: {Math.round(indicator.confidence * 100)}%
                      </div>
                      
                      {indicator.evidence && indicator.evidence.length > 0 && (
                        <div style={{ marginTop: '8px', paddingLeft: '12px', borderLeft: '2px solid rgba(255,255,255,0.1)' }}>
                          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Evidence:</div>
                          {indicator.evidence.map((ev, eIdx) => (
                            <div key={eIdx} style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                              • {formatLabel(ev.cue)}: {ev.value.toFixed(2)}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}

      {scene && (
        <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '24px', marginTop: '24px' }}>
          <h4 style={{ margin: '0 0 16px 0', fontSize: '14px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Advanced Video Intelligence
          </h4>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
            
            {/* Activity */}
            <div style={{ background: 'var(--surface-dark)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#fff', marginBottom: '12px' }}>Activity</div>
              {scene.activities.length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>No active people</div>
              ) : (
                scene.activities.map(act => (
                  <div key={act.track_id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '8px' }}>
                    <span style={{ color: '#cbd5e1' }}>Person ID {act.track_id}</span>
                    <span style={{ 
                      fontWeight: 'bold', 
                      color: act.state === 'LOITERING' ? 'var(--warning-color, #f59e0b)' : (act.state === 'MOVING' ? 'var(--success-color)' : '#94a3b8') 
                    }}>
                      {act.state.replace(/_/g, ' ')}
                    </span>
                  </div>
                ))
              )}
            </div>

            {/* Interactions */}
            <div style={{ background: 'var(--surface-dark)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#fff', marginBottom: '12px' }}>Interactions</div>
              {scene.interactions.length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>No interactions detected</div>
              ) : (
                scene.interactions.map((int, i) => (
                  <div key={i} style={{ fontSize: '13px', marginBottom: '8px', color: '#cbd5e1' }}>
                    Person {int.track_a} ↔ Person {int.track_b}
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      {int.state.replace(/_/g, ' ')}: {int.duration_seconds.toFixed(1)}s
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Anomalies */}
            {scene.anomalies.length > 0 && (
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#f87171', marginBottom: '12px' }}>Scene Anomalies</div>
                {scene.anomalies.map((anom, i) => (
                  <div key={i} style={{ fontSize: '13px', marginBottom: '8px', color: '#fca5a5' }}>
                    {anom.type.replace(/_/g, ' ')} detected
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      Confidence: {Math.round(anom.confidence * 100)}%
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {/* Heatmap visualization placeholder */}
            {scene.heatmap && (
               <div style={{ background: 'var(--surface-dark)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)', gridColumn: '1 / -1' }}>
                 <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#fff', marginBottom: '12px' }}>Motion Heatmap (Normalized)</div>
                 <div style={{ 
                   display: 'grid', 
                   gridTemplateColumns: `repeat(${scene.heatmap.grid_width}, 1fr)`, 
                   gap: '2px',
                   maxWidth: '400px',
                   margin: '0 auto'
                 }}>
                   {scene.heatmap.cells.flat().map((intensity, i) => (
                     <div key={i} style={{ 
                       paddingBottom: '100%', 
                       background: `rgba(59, 130, 246, ${intensity * 0.8 + 0.1})`,
                       borderRadius: '2px'
                     }}></div>
                   ))}
                 </div>
               </div>
            )}

          </div>
        </div>
      )}
    </div>
  );
};
