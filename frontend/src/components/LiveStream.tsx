import React, { useEffect, useRef, useState } from 'react';

const API_BASE_URL = 'http://localhost:8000/api/v1';

interface LiveStreamProps {
  cameraId: string;
  onClose: () => void;
}

export const LiveStream: React.FC<LiveStreamProps> = ({ cameraId, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const [status, setStatus] = useState<string>('Initializing WebRTC...');
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const startStream = async () => {
      try {
        const pc = new RTCPeerConnection({
          iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
        });
        pcRef.current = pc;

        pc.addTransceiver('video', { direction: 'recvonly' });

        pc.ontrack = (event) => {
          console.log('Received track:', event.track.kind);
          if (videoRef.current && event.track.kind === 'video') {
            const stream = new MediaStream([event.track]);
            videoRef.current.srcObject = stream;
            setStatus('Live Stream Connected');
          }
        };

        pc.oniceconnectionstatechange = () => {
          console.log('ICE state:', pc.iceConnectionState);
          if (pc.iceConnectionState === 'failed' || pc.iceConnectionState === 'disconnected') {
            setStatus('Connection lost');
          }
        };

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        setStatus('Gathering ICE candidates...');

        // Wait for ICE gathering to complete (trickle ICE is not fully supported by WHEP standard usually, wait for complete SDP)
        await new Promise<void>((resolve) => {
          if (pc.iceGatheringState === 'complete') {
            resolve();
          } else {
            pc.onicegatheringstatechange = () => {
              if (pc.iceGatheringState === 'complete') resolve();
            };
            // Fallback timeout in case complete state takes too long
            setTimeout(resolve, 5000);
          }
        });

        if (!active) return;

        setStatus('Sending SDP Offer to server...');
        const sdpOffer = pc.localDescription?.sdp;

        const response = await fetch(`${API_BASE_URL}/cameras/${cameraId}/live`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            // Hardcoded dev token for now
            'Authorization': 'Bearer dev_token'
          },
          body: JSON.stringify({ sdp_offer: sdpOffer })
        });

        if (!response.ok) {
          throw new Error(`Server returned ${response.status}`);
        }

        const data = await response.json();
        
        if (data.status === 'success') {
          setSessionId(data.session_id);
          setStatus('Applying SDP Answer...');
          
          await pc.setRemoteDescription(new RTCSessionDescription({
            type: 'answer',
            sdp: data.sdp_answer
          }));
        } else {
          throw new Error('Failed to start stream from provider');
        }

      } catch (err: any) {
        console.error('WebRTC Error:', err);
        setStatus(`Error: ${err.message}`);
      }
    };

    startStream();

    return () => {
      active = false;
      if (pcRef.current) {
        pcRef.current.close();
      }
      if (sessionId) {
        // Send a beacon or fetch request to stop the stream to the backend
        fetch(`${API_BASE_URL}/cameras/${cameraId}/live/${encodeURIComponent(sessionId)}`, {
          method: 'DELETE',
          headers: {
            'Authorization': 'Bearer dev_token'
          }
        }).catch(err => console.error("Error stopping stream:", err));
      }
    };
  }, [cameraId]); // Notice sessionId is intentionally omitted to avoid cleanup on sessionId change

  return (
    <div>
      <div className="flex-between">
        <h3 style={{ margin: 0 }}>Live View</h3>
        <button className="btn btn-danger" onClick={onClose}>Close Stream</button>
      </div>
      
      <div className="video-container" style={{ position: 'relative', width: '100%', height: '100%', minHeight: '300px' }}>
        <video 
          ref={videoRef} 
          autoPlay 
          playsInline 
          muted 
          controls
          style={{ width: '100%', height: '100%', display: status.includes('Live Stream Connected') ? 'block' : 'none' }}
        ></video>
        
        {!status.includes('Live Stream Connected') && (
          <div style={{ textAlign: 'center', color: '#94a3b8', position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
            <div className="loader"></div>
            <p style={{ marginTop: '1rem' }}>{status}</p>
          </div>
        )}
      </div>
    </div>
  );
};
