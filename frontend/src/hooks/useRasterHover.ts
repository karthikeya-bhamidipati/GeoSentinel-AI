import { useState, useEffect, useRef } from 'react';
import type { AnalysisResult } from '@/types';
import maplibregl from 'maplibre-gl';

export const CLASS_COLORS = [
  { name: "Urban", rgb: [220, 20, 60] },
  { name: "Vegetation", rgb: [34, 139, 34] },
  { name: "Water", rgb: [30, 144, 255] },
  { name: "Barren", rgb: [210, 180, 140] }
];

function colorDistance(r1: number, g1: number, b1: number, r2: number, g2: number, b2: number) {
  return Math.abs(r1 - r2) + Math.abs(g1 - g2) + Math.abs(b1 - b2);
}

export function useRasterHover(map: maplibregl.Map | null, result: AnalysisResult | null, layers: any[]) {
  const [hoverInfo, setHoverInfo] = useState<{x: number, y: number, className: string, area: number, date: string} | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const activeUrlRef = useRef<string | null>(null);
  const bboxRef = useRef<number[] | null>(null);

  useEffect(() => {
    if (!result || !map) return;
    
    // Check if segmentation maps are visible
    const t1Visible = layers.find(l => l.id === "segmentation_t1")?.visible;
    const t2Visible = layers.find(l => l.id === "segmentation_t2")?.visible;
    
    let activeType = "";
    if (t2Visible) activeType = "mask_t2_png";
    else if (t1Visible) activeType = "mask_t1_png";
    
    if (!activeType) {
      setHoverInfo(null);
      activeUrlRef.current = null;
      return;
    }
    
    const apiBase = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : "/api/v1";
    const url = `${apiBase}/download/${result.job_id}/${activeType}`;
    
    if (activeUrlRef.current !== url) {
      activeUrlRef.current = url;
      bboxRef.current = result.metadata?.bbox || null;
      
      const img = new Image();
      img.crossOrigin = "Anonymous";
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        if (ctx) {
          ctx.drawImage(img, 0, 0);
          canvasRef.current = canvas;
          ctxRef.current = ctx;
        }
      };
      img.src = url;
    }

    const onMouseMove = (e: any) => {
      if (!canvasRef.current || !ctxRef.current || !bboxRef.current) return;
      const [west, south, east, north] = bboxRef.current;
      
      const lng = e.lngLat.lng;
      const lat = e.lngLat.lat;
      
      if (lng < west || lng > east || lat < south || lat > north) {
        setHoverInfo(null);
        return;
      }
      
      // Calculate percentages (0 to 1)
      const px = (lng - west) / (east - west);
      const py = 1 - ((lat - south) / (north - south)); // lat goes from bottom to top, image goes top to bottom
      
      const pixelX = Math.floor(px * canvasRef.current.width);
      const pixelY = Math.floor(py * canvasRef.current.height);
      
      if (pixelX < 0 || pixelX >= canvasRef.current.width || pixelY < 0 || pixelY >= canvasRef.current.height) {
          setHoverInfo(null);
          return;
      }
      
      const pixel = ctxRef.current.getImageData(pixelX, pixelY, 1, 1).data;
      if (pixel[3] === 0 || (pixel[0]===0 && pixel[1]===0 && pixel[2]===0)) {
        setHoverInfo(null);
        return;
      }
      
      const r = pixel[0], g = pixel[1], b = pixel[2];
      
      let closestClass = null;
      let minDistance = 1000;
      for (const cls of CLASS_COLORS) {
        const d = colorDistance(r, g, b, cls.rgb[0], cls.rgb[1], cls.rgb[2]);
        if (d < minDistance) {
          minDistance = d;
          closestClass = cls.name;
        }
      }
      
      if (closestClass && minDistance < 50) {
        const dateStr = activeType === "mask_t2_png" ? "T2" : "T1";
        const areaKey = activeType === "mask_t2_png" ? "t2_area_km2" : "t1_area_km2";
        
        // Look up area from result.area_change.rows
        let area = 0;
        const rows = result.area_change?.rows;
        if (rows && Array.isArray(rows)) {
          const row = rows.find((r: any) => r.class_name === closestClass);
          if (row) {
            area = row[areaKey] || 0;
          }
        }
        
        setHoverInfo({
          x: e.point.x,
          y: e.point.y,
          className: closestClass,
          area: Number(area.toFixed(2)),
          date: dateStr
        });
      } else {
        setHoverInfo(null);
      }
    };

    map.on('mousemove', onMouseMove);
    return () => { map.off('mousemove', onMouseMove); };
  }, [map, result, layers]);

  return hoverInfo;
}
