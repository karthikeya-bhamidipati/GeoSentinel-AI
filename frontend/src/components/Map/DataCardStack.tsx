'use client';

// =============================================================================
// GeoSentinel AI — DataCardStack
// Draggable layer cards controlling map layer Z-index ordering
// =============================================================================

import React, { useState } from 'react';
import { Reorder, useDragControls, motion } from 'framer-motion';
import { Layer } from '@/hooks/useMap';

interface DataCardStackProps {
  layers: Layer[];
  onToggleLayer: (layerId: string) => void;
  onReorderLayers: (reorderedLayers: Layer[]) => void;
}

interface LayerOpacity {
  [layerId: string]: number;
}

function DragHandleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="4" cy="3" r="1.2" fill="currentColor" />
      <circle cx="10" cy="3" r="1.2" fill="currentColor" />
      <circle cx="4" cy="7" r="1.2" fill="currentColor" />
      <circle cx="10" cy="7" r="1.2" fill="currentColor" />
      <circle cx="4" cy="11" r="1.2" fill="currentColor" />
      <circle cx="10" cy="11" r="1.2" fill="currentColor" />
    </svg>
  );
}

function EyeIcon({ visible }: { visible: boolean }) {
  if (visible) {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    );
  }
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );
}

function DataCard({
  layer,
  onToggle,
  opacity,
  onOpacityChange,
}: {
  layer: Layer;
  onToggle: () => void;
  opacity: number;
  onOpacityChange: (val: number) => void;
}) {
  const dragControls = useDragControls();

  return (
    <Reorder.Item
      value={layer}
      dragListener={false}
      dragControls={dragControls}
      className={`data-card ${layer.visible ? 'active' : ''}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        padding: '10px 12px',
        borderRadius: '10px',
        marginBottom: '6px',
        background: 'rgba(15, 20, 30, 0.7)',
        backdropFilter: 'blur(12px)',
        border: layer.visible
          ? '1px solid rgba(0, 255, 255, 0.3)'
          : '1px solid rgba(255, 255, 255, 0.06)',
        boxShadow: layer.visible
          ? '0 0 15px rgba(0, 255, 255, 0.08), inset 0 0 20px rgba(0, 255, 255, 0.02)'
          : 'none',
        cursor: 'default',
        transition: 'border-color 0.3s, box-shadow 0.3s',
        listStyle: 'none',
      }}
      whileHover={{ scale: 1.01 }}
      layout
      transition={{ type: 'spring', damping: 25, stiffness: 300 }}
    >
      {/* Drag handle */}
      <div
        className="data-card-handle"
        onPointerDown={(e) => dragControls.start(e)}
        style={{
          cursor: 'grab',
          color: 'rgba(255, 255, 255, 0.3)',
          display: 'flex',
          alignItems: 'center',
          touchAction: 'none',
        }}
      >
        <DragHandleIcon />
      </div>

      {/* Color dot */}
      <div
        style={{
          width: '10px',
          height: '10px',
          borderRadius: '50%',
          background: layer.color,
          flexShrink: 0,
          boxShadow: layer.visible ? `0 0 8px ${layer.color}60` : 'none',
        }}
      />

      {/* Layer info */}
      <div className="data-card-info" style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: '0.78rem',
            fontWeight: 600,
            color: layer.visible ? 'rgba(255, 255, 255, 0.9)' : 'rgba(255, 255, 255, 0.4)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            transition: 'color 0.3s',
          }}
        >
          {layer.name}
        </div>

        {/* Opacity slider */}
        {layer.visible && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            style={{ marginTop: '4px' }}
          >
            <input
              type="range"
              min={0}
              max={100}
              value={opacity}
              onChange={(e) => onOpacityChange(Number(e.target.value))}
              style={{
                width: '100%',
                height: '3px',
                appearance: 'none',
                background: `linear-gradient(to right, rgba(0,255,255,0.6) ${opacity}%, rgba(255,255,255,0.1) ${opacity}%)`,
                borderRadius: '2px',
                outline: 'none',
                cursor: 'pointer',
              }}
            />
          </motion.div>
        )}
      </div>

      {/* Visibility toggle */}
      <button
        onClick={onToggle}
        style={{
          background: 'none',
          border: 'none',
          color: layer.visible ? '#00ffff' : 'rgba(255, 255, 255, 0.2)',
          cursor: 'pointer',
          padding: '4px',
          display: 'flex',
          alignItems: 'center',
          transition: 'color 0.3s',
        }}
        aria-label={`Toggle ${layer.name} visibility`}
      >
        <EyeIcon visible={layer.visible} />
      </button>
    </Reorder.Item>
  );
}

export default function DataCardStack({
  layers,
  onToggleLayer,
  onReorderLayers,
}: DataCardStackProps) {
  const analysisLayers = layers.filter((l) => l.type === 'analysis');
  const [opacities, setOpacities] = useState<LayerOpacity>(() => {
    const init: LayerOpacity = {};
    analysisLayers.forEach((l) => (init[l.id] = 100));
    return init;
  });

  const handleOpacityChange = (layerId: string, value: number) => {
    setOpacities((prev) => ({ ...prev, [layerId]: value }));
  };

  const handleReorder = (reordered: Layer[]) => {
    // Merge reordered analysis layers back into the full layers array
    const nonAnalysis = layers.filter((l) => l.type !== 'analysis');
    onReorderLayers([...nonAnalysis, ...reordered]);
  };

  if (analysisLayers.length === 0) {
    return null;
  }

  return (
    <motion.div
      className="data-card-stack"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
      style={{
        position: 'absolute',
        top: '80px',
        left: '16px',
        width: '260px',
        zIndex: 500,
        padding: '12px',
        borderRadius: '14px',
        background: 'rgba(10, 14, 20, 0.75)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(0, 255, 255, 0.08)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
      }}
    >
      <div
        style={{
          fontSize: '0.7rem',
          fontWeight: 700,
          color: 'rgba(0, 255, 255, 0.6)',
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          marginBottom: '10px',
          paddingLeft: '4px',
        }}
      >
        Analysis Layers
      </div>
      <Reorder.Group
        axis="y"
        values={analysisLayers}
        onReorder={handleReorder}
        style={{ padding: 0, margin: 0 }}
      >
        {analysisLayers.map((layer) => (
          <DataCard
            key={layer.id}
            layer={layer}
            onToggle={() => onToggleLayer(layer.id)}
            opacity={opacities[layer.id] ?? 100}
            onOpacityChange={(val) => handleOpacityChange(layer.id, val)}
          />
        ))}
      </Reorder.Group>
    </motion.div>
  );
}
