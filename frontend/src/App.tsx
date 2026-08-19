import { useEffect, useState } from 'react'
import { LiveStream } from './components/LiveStream'
import './index.css'

interface Camera {
  camera_id: string;
  name: string;
  status: string;
  location: string | null;
  capabilities: Record<string, any>;
  last_event: any | null;
}

function App() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [isLive, setIsLive] = useState(false);

  const fetchCameras = async () => {
    try {
      setLoading(true);
      const res = await fetch('http://localhost:8000/api/v1/cameras', {
        headers: {
          'Authorization': 'Bearer dev_token'
        }
      });
      const data = await res.json();
      setCameras(data);
    } catch (err) {
      console.error("Failed to fetch cameras", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, []);

  const handleSelectCamera = (cam: Camera) => {
    setSelectedCamera(cam);
    setIsLive(false);
  };

  return (
    <div className="dashboard">
      <header className="header">
        <h1>XCEL Vision Dashboard</h1>
      </header>

      {loading ? (
        <div style={{ textAlign: 'center', marginTop: '4rem' }}>
          <div className="loader"></div>
          <p>Discovering Cameras...</p>
        </div>
      ) : (
        <div className="grid">
          {cameras.map(cam => (
            <div 
              key={cam.camera_id} 
              className="glass-card" 
              onClick={() => handleSelectCamera(cam)}
              style={{
                borderColor: selectedCamera?.camera_id === cam.camera_id ? 'var(--accent-color)' : 'var(--card-border)'
              }}
            >
              <h3>
                <span className={`status-indicator status-${cam.status.toLowerCase()}`}></span>
                {cam.name}
              </h3>
              <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1rem' }}>
                {cam.location || 'Unknown Location'}
              </p>
              <div>
                {Object.keys(cam.capabilities).slice(0, 4).map(cap => (
                  <span key={cap} className="badge">{cap}</span>
                ))}
                {Object.keys(cam.capabilities).length > 4 && (
                  <span className="badge">+{Object.keys(cam.capabilities).length - 4} more</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedCamera && !isLive && (
        <div className="detail-view">
          <div className="flex-between" style={{ marginBottom: '1.5rem' }}>
            <h2>{selectedCamera.name} Details</h2>
            <button className="btn" onClick={() => setIsLive(true)}>
              Start Live View
            </button>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
            <div>
              <h4 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Capabilities</h4>
              <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                {Object.keys(selectedCamera.capabilities).map(cap => (
                  <li key={cap}>{cap}: {String(selectedCamera.capabilities[cap])}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>System Info</h4>
              <p style={{ margin: '0 0 0.5rem 0' }}><strong>ID:</strong> {selectedCamera.camera_id}</p>
              <p style={{ margin: '0 0 0.5rem 0' }}><strong>Status:</strong> {selectedCamera.status}</p>
              <p style={{ margin: '0 0 0.5rem 0' }}><strong>Location:</strong> {selectedCamera.location || 'N/A'}</p>
            </div>
          </div>
        </div>
      )}

      {selectedCamera && isLive && (
        <div className="detail-view">
          <LiveStream 
            cameraId={selectedCamera.camera_id} 
            onClose={() => setIsLive(false)} 
          />
        </div>
      )}
    </div>
  )
}

export default App
