import React, { useEffect, useState } from 'react';
import { usePerformance } from '../../context/PerformanceContext';

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  formatter?: (val: number) => string;
}

export const AnimatedCounter: React.FC<AnimatedCounterProps> = ({
  value,
  duration = 800,
  formatter = (v) => (v < 10 ? `0${v}` : `${v}`),
}) => {
  const { mode } = usePerformance();
  const [displayValue, setDisplayValue] = useState<number>(() =>
    mode === 'reduced' ? value : 0
  );

  useEffect(() => {
    if (mode === 'reduced') {
      setDisplayValue(value);
      return;
    }

    let start = 0;
    const startTime = performance.now();

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out quad
      const easedProgress = progress * (2 - progress);
      const current = Math.floor(easedProgress * value);

      setDisplayValue(current);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setDisplayValue(value);
      }
    };

    const animId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animId);
  }, [value, duration, mode]);

  return <span>{formatter(displayValue)}</span>;
};
