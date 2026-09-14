import '@testing-library/jest-dom';

// Minimal canvas 2d context mock for Cytoscape in jsdom environment (Section 53)
if (typeof HTMLCanvasElement !== 'undefined') {
  HTMLCanvasElement.prototype.getContext = (() => ({
    fillRect: () => {},
    clearRect: () => {},
    getImageData: () => ({ data: new Uint8ClampedArray(0) } as unknown as ImageData),
    putImageData: () => {},
    createImageData: () => ({ data: new Uint8ClampedArray(0) } as unknown as ImageData),
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
    measureText: () => ({ width: 0 } as unknown as TextMetrics),
    transform: () => {},
    rect: () => {},
    clip: () => {}
  })) as unknown as typeof HTMLCanvasElement.prototype.getContext;
}

// Minimal element dimension getters for jsdom environment (Section 53)
if (typeof HTMLElement !== 'undefined') {
  Object.defineProperty(HTMLElement.prototype, 'clientWidth', {
    configurable: true,
    get: function () {
      return 800;
    }
  });
  Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
    configurable: true,
    get: function () {
      return 600;
    }
  });
}

// Minimal ResizeObserver mock for jsdom environment
if (typeof global !== 'undefined' && !global.ResizeObserver) {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}
