import React, { useEffect, useRef, useState, useCallback } from 'react';
import { PeopleCount } from './PeopleCount';
import type { AIStatus } from './PeopleCount';

const API_BASE_URL = 'http://localhost:8000/api/v1';

interface LiveStreamProps {
  cameraId: string;
  onClose: () => void;
}

export const LiveStream: React.FC<LiveStreamProps> = ({ cameraId, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const [status, setStatus] = useState<string>('Initializing WebRTC...');
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // AI State
  const [aiStatus, setAiStatus] = useState<AIStatus>('analyzing');
  const [peopleCount, setPeopleCount] = useState<number | null>(null);
  const aiSessionIdRef = useRef<string>(Math.random().toString(36).substring(2, 15));
  const aiLoopActiveRef = useRef<boolean>(false);
  const aiRequestInFlightRef = useRef<boolean>(false);

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

    // AI Frame Sampling Loop
    const runAILoop = async () => {
      if (!active || !aiLoopActiveRef.current) return;
      
      // Backpressure: only one in flight
      if (!aiRequestInFlightRef.current && videoRef.current && canvasRef.current && videoRef.current.readyState >= 2) {
        aiRequestInFlightRef.current = true;
        
        try {
          const video = videoRef.current;
          const canvas = canvasRef.current;
          const ctx = canvas.getContext('2d');
          
          if (ctx) {
            // Downsample slightly to save bandwidth and backend processing
            canvas.width = 640;
            canvas.height = (video.videoHeight / video.videoWidth) * 640 || 480;
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            const blob = await new Promise<Blob | null>(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8));
            
            if (blob) {
              const formData = new FormData();
              formData.append('file', blob, 'frame.jpg');
              formData.append('session_id', aiSessionIdRef.current);
              
              const res = await fetch(`${API_BASE_URL}/cameras/${cameraId}/analyze-frame`, {
                method: 'POST',
                headers: {
                  'Authorization': 'Bearer dev_token'
                },
                body: formData
              });
              
              if (res.ok) {
                const data = await res.json();
                setPeopleCount(data.persons);
                setAiStatus('live');
              } else {
                console.error("AI inference error:", res.status);
                setAiStatus('unavailable');
              }
            }
          }
        } catch (err) {
          console.error("AI frame submission error:", err);
          setAiStatus('unavailable');
        } finally {
          aiRequestInFlightRef.current = false;
        }
      }
      
      // Schedule next frame check regardless of success/failure (bounded sampling ~ 2-3 fps)
      setTimeout(runAILoop, 400); 
    };

    // Start loop immediately; it will wait for video readyState internally
    aiLoopActiveRef.current = true;
    runAILoop();

    return () => {
      active = false;
      aiLoopActiveRef.current = false;
      if (pcRef.current) {
        pcRef.current.close();
      }
      if (sessionId) {
        // Send a beacon or fetch request to stop the stream to the backend
        // We pass the aiSessionId as the session to cleanup, but wait, the backend uses sessionId to cleanup WHEP and AI together.
        // Actually we need to make sure the AI session ID is also cleaned up. Let's append it to the URL query or path if we want,
        // but for MVP we mapped it to `stop_live_stream(camera_id, session_id)`. The WHEP session ID was used there!
        // Wait, the backend /analyze-frame accepts `session_id`. So AI tracking uses `aiSessionId`.
        // Let's pass both to the backend to cleanup.
        fetch(`${API_BASE_URL}/cameras/${cameraId}/live/${encodeURIComponent(sessionId)}?ai_session_id=${encodeURIComponent(aiSessionIdRef.current)}`, {
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
        
        {/* Hidden canvas for frame extraction */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {status.includes('Live Stream Connected') && (
          <div style={{ position: 'absolute', bottom: '20px', left: '20px', zIndex: 10 }}>
            <PeopleCount count={peopleCount} status={aiStatus} />
          </div>
        )}

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
