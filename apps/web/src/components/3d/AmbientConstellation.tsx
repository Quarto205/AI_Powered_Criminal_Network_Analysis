import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { usePerformance } from '../../context/PerformanceContext';

interface NetworkConstellationProps {
  interactive?: boolean;
  count?: number;
}

const ConstellationMesh: React.FC<{ count: number }> = ({ count }) => {
  const pointsRef = useRef<THREE.Points>(null!);
  const linesRef = useRef<THREE.LineSegments>(null!);
  const mouse = useRef({ x: 0, y: 0 });

  // Generate steady nodes
  const { positions, linePositions } = useMemo(() => {
    const coords: number[] = [];
    const pts: THREE.Vector3[] = [];

    // Spherical / orbital distribution with gentle clustering
    for (let i = 0; i < count; i++) {
      const radius = 2.5 + Math.random() * 2.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      const x = radius * Math.sin(phi) * Math.cos(theta);
      const y = radius * Math.sin(phi) * Math.sin(theta);
      const z = radius * Math.cos(phi);

      coords.push(x, y, z);
      pts.push(new THREE.Vector3(x, y, z));
    }

    // Connect close neighbors
    const lineCoords: number[] = [];
    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        const dist = pts[i].distanceTo(pts[j]);
        if (dist < 2.0) {
          lineCoords.push(pts[i].x, pts[i].y, pts[i].z);
          lineCoords.push(pts[j].x, pts[j].y, pts[j].z);
        }
      }
    }

    return {
      positions: new Float32Array(coords),
      linePositions: new Float32Array(lineCoords),
    };
  }, [count]);

  useFrame((state, delta) => {
    if (pointsRef.current) {
      pointsRef.current.rotation.y += delta * 0.08;
      pointsRef.current.rotation.x += delta * 0.03;
    }
    if (linesRef.current) {
      linesRef.current.rotation.y += delta * 0.08;
      linesRef.current.rotation.x += delta * 0.03;
    }
  });

  return (
    <group>
      {/* Network Nodes */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[positions, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.07}
          color="#2563eb"
          transparent
          opacity={0.85}
          sizeAttenuation
        />
      </points>

      {/* Network Interconnection Lines */}
      <lineSegments ref={linesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[linePositions, 3]}
          />
        </bufferGeometry>
        <lineBasicMaterial
          color="#3b82f6"
          transparent
          opacity={0.22}
        />
      </lineSegments>
    </group>
  );
};

export const AmbientConstellation: React.FC<NetworkConstellationProps> = ({ count = 48 }) => {
  const { is3dEnabled, mode } = usePerformance();

  if (!is3dEnabled) {
    return (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'radial-gradient(circle at center, rgba(37,99,235,0.06) 0%, transparent 70%)',
        }}
      />
    );
  }

  const effectiveCount = mode === 'balanced' ? Math.min(count, 24) : count;

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Canvas
        camera={{ position: [0, 0, 7], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ pointerEvents: 'none' }}
      >
        <ambientLight intensity={0.8} />
        <ConstellationMesh count={effectiveCount} />
      </Canvas>
    </div>
  );
};
