import React from 'react';

export interface AnalyticsData {
  visible_people: number;
  initial_occupancy: number;
  total_entries: number;
  total_exits: int;
  estimated_occupancy: number;
  average_dwell_time_seconds: number;
}

interface AnalyticsDisplayProps {
  data: AnalyticsData | null;
}

export const AnalyticsDisplay: React.FC<AnalyticsDisplayProps> = ({ data }) => {
  if (!data) return null;
  
  return (
    <div style={{
      background: 'rgba(15, 23, 42, 0.85)',
      backdropFilter: 'blur(8px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '8px',
      padding: '16px',
      color: '#fff',
      fontFamily: 'Inter, sans-serif',
      minWidth: '220px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
    }}>
      <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Session Analytics
      </h4>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div>
          <div style={{ fontSize: '11px', color: '#cbd5e1' }}>Visible People</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{data.visible_people}</div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: '#cbd5e1' }}>Occupancy</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#3b82f6' }}>{data.estimated_occupancy}</div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: '#cbd5e1' }}>Entries</div>
          <div style={{ fontSize: '16px', fontWeight: '600', color: '#10b981' }}>{data.total_entries}</div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: '#cbd5e1' }}>Exits</div>
          <div style={{ fontSize: '16px', fontWeight: '600', color: '#ef4444' }}>{data.total_exits}</div>
        </div>
        <div style={{ gridColumn: 'span 2' }}>
          <div style={{ fontSize: '11px', color: '#cbd5e1' }}>Avg Dwell Time</div>
          <div style={{ fontSize: '16px', fontWeight: '600' }}>{data.average_dwell_time_seconds.toFixed(1)}s</div>
        </div>
      </div>
    </div>
  );
};
