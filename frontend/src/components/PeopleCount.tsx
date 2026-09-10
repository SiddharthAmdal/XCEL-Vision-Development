import React from 'react';

export type AIStatus = 'analyzing' | 'live' | 'unavailable';

export interface PeopleCountProps {
  count: number | null;
  status: AIStatus;
  facesCount?: number | null;
  expressions?: Record<string, number> | null;
}

export const PeopleCount: React.FC<PeopleCountProps> = ({ count, status, facesCount, expressions }) => {
  let displayContent;

  switch (status) {
    case 'unavailable':
      displayContent = <span style={{ color: '#ef4444' }}>AI unavailable</span>;
      break;
    case 'analyzing':
      displayContent = <span style={{ color: '#eab308' }}>Analyzing...</span>;
      break;
    case 'live':
      if (count === null) {
        displayContent = <span style={{ color: '#eab308' }}>Analyzing...</span>;
      } else {
        displayContent = (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span>
              <span style={{ fontWeight: 'bold' }}>{count}</span>
              {count === 1 ? ' Person' : ' People'}
            </span>
            {facesCount !== undefined && facesCount !== null && (
              <span style={{ fontSize: '0.8rem', opacity: 0.9, marginTop: '2px' }}>
                <span style={{ fontWeight: 'bold' }}>{facesCount}</span>
                {facesCount === 1 ? ' Face detected' : ' Faces detected'}
              </span>
            )}
            {expressions && Object.keys(expressions).length > 0 && (
              <div style={{ marginTop: '4px', fontSize: '0.8rem', borderTop: '1px solid rgba(255,255,255,0.2)', paddingTop: '4px' }}>
                <div style={{ opacity: 0.8, marginBottom: '2px' }}>Expressions:</div>
                {Object.entries(expressions).map(([label, count]) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', marginLeft: '4px' }}>
                    <span>{label}:</span>
                    <span style={{ fontWeight: 'bold' }}>{count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      }
      break;
  }

  return (
    <div 
      className="people-count-indicator"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        background: 'rgba(0, 0, 0, 0.7)',
        padding: '0.5rem 1rem',
        borderRadius: '8px',
        color: '#fff',
        fontSize: '0.9rem',
        backdropFilter: 'blur(4px)',
        border: '1px solid rgba(255,255,255,0.1)'
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {displayContent}
      </div>
    </div>
  );
};
