export function scaleBoundingBox(
  x1: number, y1: number, x2: number, y2: number,
  analysisW: number, analysisH: number,
  canvasW: number, canvasH: number,
  videoW: number, videoH: number
): [number, number, number, number] {
  const videoRatio = videoW / videoH;
  const elementRatio = canvasW / canvasH;

  let renderWidth = canvasW;
  let renderHeight = canvasH;
  let offsetX = 0;
  let offsetY = 0;

  if (videoRatio > elementRatio) {
    renderHeight = canvasW / videoRatio;
    offsetY = (canvasH - renderHeight) / 2;
  } else {
    renderWidth = canvasH * videoRatio;
    offsetX = (canvasW - renderWidth) / 2;
  }

  const scaleX = renderWidth / analysisW;
  const scaleY = renderHeight / analysisH;

  let canvasX1 = (x1 * scaleX) + offsetX;
  let canvasY1 = (y1 * scaleY) + offsetY;
  let canvasX2 = (x2 * scaleX) + offsetX;
  let canvasY2 = (y2 * scaleY) + offsetY;

  // Clamping
  canvasX1 = Math.max(0, Math.min(canvasX1, canvasW));
  canvasY1 = Math.max(0, Math.min(canvasY1, canvasH));
  canvasX2 = Math.max(0, Math.min(canvasX2, canvasW));
  canvasY2 = Math.max(0, Math.min(canvasY2, canvasH));

  return [canvasX1, canvasY1, canvasX2, canvasY2];
}
