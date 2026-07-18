export const IT_CORRIDOR_ZONE = {
  type: "Feature" as const,
  properties: { name: "IT Corridor", color: "#38bdf8" },
  geometry: {
    type: "Polygon" as const,
    coordinates: [[[78.33, 17.42], [78.39, 17.42], [78.39, 17.46], [78.33, 17.46], [78.33, 17.42]]]
  }
};

export const OLD_CITY_ZONE = {
  type: "Feature" as const,
  properties: { name: "Old City", color: "#fbbf24" },
  geometry: {
    type: "Polygon" as const,
    coordinates: [[[78.46, 17.34], [78.50, 17.34], [78.50, 17.38], [78.46, 17.38], [78.46, 17.34]]]
  }
};

export const HUSSAIN_SAGAR_CENTER: [number, number] = [17.4239, 78.4738];
export const OSMAN_SAGAR_CENTER: [number, number] = [17.3713, 78.3075];

export interface HotspotTemplate {
  name: string;
  description: string;
  center: [number, number];
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
}

export const HYDERABAD_HOTSPOT_TEMPLATES: HotspotTemplate[] = [
  { name: 'Gachibowli IT Corridor', description: 'Rapid commercial expansion replacing agricultural land', center: [17.44, 78.35], severity: 'HIGH' },
  { name: 'Kokapet-Narsingi Belt', description: 'Massive residential development on former farmland', center: [17.39, 78.34], severity: 'CRITICAL' },
  { name: 'Hussain Sagar Periphery', description: 'Encroachment on lake buffer zones', center: [17.43, 78.47], severity: 'HIGH' },
  { name: 'Shamshabad Airport Zone', description: 'Aerotropolis development converting agricultural land', center: [17.24, 78.43], severity: 'MEDIUM' },
  { name: 'ORR Eastern Arc', description: 'Urban sprawl along Outer Ring Road', center: [17.35, 78.55], severity: 'MEDIUM' },
];
