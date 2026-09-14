import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Automatically unmount and cleanup DOM between tests
afterEach(() => {
  cleanup();
});

// Provide full 2d canvas mock for Cytoscape in jsdom environment
if (typeof HTMLCanvasElement !== 'undefined') {
  const dummyCtx: Record<string, any> = {
    fillRect: () => {},
    clearRect: () => {},
    getImageData: () => ({ data: new Array(4) }),
    putImageData: () => {},
    createImageData: () => [],
    setTransform: () => {},
    drawImage: () => {},
    save: () => {},
    fillText: () => {},
    restore: () => {},
    beginPath: () => {},
    moveTo: () => {},
    lineTo: () => {},
    closePath: () => {},
    stroke: () => {},
    translate: () => {},
    scale: () => {},
    rotate: () => {},
    arc: () => {},
    fill: () => {},
    measureText: () => ({ width: 10, actualBoundingBoxAscent: 10, actualBoundingBoxDescent: 2 }),
    transform: () => {},
    rect: () => {},
    clip: () => {},
    strokeRect: () => {},
    quadraticCurveTo: () => {},
    bezierCurveTo: () => {},
    arcTo: () => {},
    isPointInPath: () => false,
    createLinearGradient: () => ({ addColorStop: () => {} }),
    createRadialGradient: () => ({ addColorStop: () => {} }),
    createPattern: () => null,
  };

  HTMLCanvasElement.prototype.getContext = function (type: string) {
    if (type === '2d') {
      return dummyCtx as any;
    }
    return null;
  };
}
