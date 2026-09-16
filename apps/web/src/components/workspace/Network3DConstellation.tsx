import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Sphere, Line, Text } from '@react-three/drei';
import * as THREE from 'three';
import { EntityDossier, NetworkEdge, EntityType } from '../../types';

export const NODE_COLOR_MAP: Record<EntityType, { bg: string; border: string; text: string; lightBg: string }> = {
  PERSON: { bg: '#2563EB', border: '#1D4ED8', text: '#FFFFFF', lightBg: '#EEF5FF' },
  PHONE: { bg: '#0891B2', border: '#0E7490', text: '#FFFFFF', lightBg: '#ECFEFF' },
  ACCOUNT: { bg: '#16A34A', border: '#15803D', text: '#FFFFFF', lightBg: '#F0FDF4' },
  COMPANY: { bg: '#0F766E', border: '#115E59', text: '#FFFFFF', lightBg: '#F0FDFA' },
  EVENT: { bg: '#EA580C', border: '#C2410C', text: '#FFFFFF', lightBg: '#FFF7ED' },
  SHELL_COMPANY: { bg: '#0F766E', border: '#115E59', text: '#FFFFFF', lightBg: '#F0FDFA' },
  BANK_ACCOUNT: { bg: '#16A34A', border: '#15803D', text: '#FFFFFF', lightBg: '#F0FDF4' },
  CRYPTO_WALLET: { bg: '#8B5CF6', border: '#7C3AED', text: '#FFFFFF', lightBg: '#F5F3FF' },
  LOGISTICS_HUB: { bg: '#4F46E5', border: '#4338CA', text: '#FFFFFF', lightBg: '#EEF2FF' },
};

interface Network3DProps {
  nodes: (EntityDossier & { x: number; y: number; z?: number })[];
  edges: NetworkEdge[];
  onNodeClick: (node: EntityDossier) => void;
}

const NodeMesh = ({ node, onClick }: { node: EntityDossier & { x: number; y: number; z?: number }; onClick: () => void }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const colors = NODE_COLOR_MAP[node.type] || NODE_COLOR_MAP.PERSON;
  
  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.01;
    }
  });

  return (
    <group position={[node.x, node.y, node.z || 0]} onClick={onClick}>
      <Sphere ref={meshRef} args={[0.6, 32, 32]}>
        <meshStandardMaterial color={colors.bg} metalness={0.1} roughness={0.2} />
      </Sphere>
      <Text position={[0, -1.2, 0]} fontSize={0.35} color="#1e293b" anchorX="center" anchorY="middle" outlineWidth={0.02} outlineColor="#ffffff">
        {node.name}
      </Text>
    </group>
  );
};

const EdgeMesh = ({ start, end, isPredicted }: { start: THREE.Vector3; end: THREE.Vector3; isPredicted: boolean }) => {
  return (
    <Line
      points={[start, end]}
      color={isPredicted ? "#A855F7" : "#cbd5e1"}
      lineWidth={isPredicted ? 2 : 1}
      dashed={isPredicted}
      dashSize={0.5}
      dashScale={0.5}
    />
  );
};

const Scene = ({ nodes, edges, onNodeClick }: Network3DProps) => {
  const { scene } = useThree();
  
  useMemo(() => {
    scene.background = new THREE.Color(0xf4f7fb); // Light background for Calm Intelligence theme
  }, [scene]);

  return (
    <>
      <ambientLight intensity={1.2} />
      <directionalLight position={[10, 20, 10]} intensity={1.5} />
      <gridHelper args={[100, 100, 0xd0dbe7, 0xe2eaf2]} position={[0, -10, 0]} />
      
      {edges.map(edge => {
        const sourceNode = nodes.find(n => n.id === edge.source);
        const targetNode = nodes.find(n => n.id === edge.target);
        if (!sourceNode || !targetNode) return null;
        
        return (
          <EdgeMesh 
            key={edge.id}
            start={new THREE.Vector3(sourceNode.x, sourceNode.y, sourceNode.z || 0)}
            end={new THREE.Vector3(targetNode.x, targetNode.y, targetNode.z || 0)}
            isPredicted={edge.epistemicType === 'AI_INFERRED'}
          />
        );
      })}
      
      {nodes.map(node => (
        <NodeMesh key={node.id} node={node} onClick={() => onNodeClick(node)} />
      ))}
      
      <OrbitControls makeDefault enableDamping dampingFactor={0.05} autoRotate autoRotateSpeed={0.5} />
    </>
  );
};

export const Network3DConstellation: React.FC<Network3DProps> = (props) => {
  return (
    <Canvas camera={{ position: [0, 5, 25], fov: 50 }} style={{ width: '100%', height: '100%' }}>
      <Scene {...props} />
    </Canvas>
  );
};
