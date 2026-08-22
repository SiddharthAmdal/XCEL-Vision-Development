import React, { useEffect, useRef, useState } from 'react';
import { scaleBoundingBox } from '../utils/boxMath';

export interface Detection {
  track_id: number;
  class_name: string;
  confidence: number;
  bounding_box: [number, number, number, number]; // x1, y1, x2, y2
}

interface PersonOverlayProps {
  detections: Detection[];
  videoRef: React.RefObject<HTMLVideoElement>;
  analysisWidth: number;
  analysisHeight: number;
}

export const PersonOverlay: React.FC<PersonOverlayProps> = ({
  detections,
  videoRef,
  analysisWidth,
  analysisHeight
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // Stable track_id to Person N mapping for this session
  const [personMapping] = useState<Record<number, number>>({});
  const nextPersonNum = useRef<number>(1);

  useEffect(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    let animationFrameId: number;
    let observer: ResizeObserver;

    const resizeCanvas = () => {
      // The video element's actual visual size on screen
      const rect = video.getBoundingClientRect();
      if (canvas.width !== rect.width || canvas.height !== rect.height) {
        canvas.width = rect.width;
        canvas.height = rect.height;
      }
    };

    const draw = () => {
      resizeCanvas();
      
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Clear previous frame
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (detections.length === 0 || analysisWidth === 0 || analysisHeight === 0) {
        return;
      }

      const videoW = video.videoWidth || canvas.width;
      const videoH = video.videoHeight || canvas.height;

      detections.forEach(det => {
        // Get or assign stable Person Number
        let personNum = personMapping[det.track_id];
        if (!personNum) {
          personNum = nextPersonNum.current++;
          personMapping[det.track_id] = personNum;
        }

        const [x1, y1, x2, y2] = det.bounding_box;
        
        // Map to canvas coordinates
        const [canvasX1, canvasY1, canvasX2, canvasY2] = scaleBoundingBox(
          x1, y1, x2, y2,
          analysisWidth, analysisHeight,
          canvas.width, canvas.height,
          videoW, videoH
        );

        const boxWidth = canvasX2 - canvasX1;
        const boxHeight = canvasY2 - canvasY1;

        if (boxWidth <= 0 || boxHeight <= 0) return;

        // Draw Bounding Box (subtle)
        ctx.strokeStyle = 'rgba(59, 130, 246, 0.8)'; // Blue-500
        ctx.lineWidth = 2;
        ctx.strokeRect(canvasX1, canvasY1, boxWidth, boxHeight);

        // Draw Label Background
        const labelText = `Person ${personNum} · #${det.track_id}`;
        ctx.font = '12px "Inter", sans-serif';
        const textMetrics = ctx.measureText(labelText);
        const textWidth = textMetrics.width;
        const textHeight = 14;
        
        ctx.fillStyle = 'rgba(15, 23, 42, 0.75)'; // Slate-900 transparent
        ctx.fillRect(canvasX1, canvasY1 - textHeight - 4, textWidth + 8, textHeight + 4);

        // Draw Label Text
        ctx.fillStyle = '#ffffff';
        ctx.textBaseline = 'bottom';
        ctx.fillText(labelText, canvasX1 + 4, canvasY1 - 2);
      });
    };

    // The detections prop changes whenever a new frame is processed.
    // We draw immediately when detections update, and also handle resizes via ResizeObserver.
    draw();

    observer = new ResizeObserver(() => {
      // Use requestAnimationFrame for smooth resize redraws
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      animationFrameId = requestAnimationFrame(draw);
    });
    
    observer.observe(video);

    return () => {
      observer.disconnect();
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    };
  }, [detections, analysisWidth, analysisHeight, personMapping, videoRef]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 5
      }}
    />
  );
};
