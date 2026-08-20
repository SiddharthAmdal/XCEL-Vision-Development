import React from 'react';

export type AIStatus = 'analyzing' | 'live' | 'unavailable';

export interface PeopleCountProps {
  count: number | null;
  status: AIStatus;
}

export const PeopleCount: React.FC<PeopleCountProps> = ({ count, status }) => {
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
          <span>
            <span style={{ fontWeight: 'bold' }}>{count}</span>
            {count === 1 ? ' Person' : ' People'}
          </span>
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
      <span style={{ marginRight: '8px', opacity: 0.8 }}>People in frame:</span>
      {displayContent}
    </div>
  );
};
