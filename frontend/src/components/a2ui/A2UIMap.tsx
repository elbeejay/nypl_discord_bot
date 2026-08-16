import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { MapPin, Navigation } from 'lucide-react';
import type { MapData as A2UIMapData } from '../../types/a2ui';

interface Props {
  data: A2UIMapData;
}

// Custom NYPL / NYC Data SVG Pin
const createCustomPin = (category?: string) => {
  const isLibrary = category?.toLowerCase().includes('library') || category?.toLowerCase().includes('nypl');
  const isFood = category?.toLowerCase().includes('restaurant') || category?.toLowerCase().includes('food');
  const color = isLibrary ? '#B8860B' : isFood ? '#2563EB' : '#D41B2C';
  const emoji = isLibrary ? '📚' : isFood ? '🍽️' : '📍';

  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div style="
        background: ${color};
        color: #fff;
        width: 30px;
        height: 30px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 3px 8px rgba(0,0,0,0.3);
        border: 2px solid #FFFFFF;
      ">
        <span style="transform: rotate(45deg); font-size: 13px; margin-bottom: 2px;">${emoji}</span>
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -28],
  });
};

export const A2UIMap: React.FC<Props> = ({ data }) => {
  const centerLat = data.center_lat || 40.7128;
  const centerLng = data.center_lng || -74.0060;
  const zoom = data.zoom || 12;
  const markers = data.markers || [];

  return (
    <div className="a2ui-card a2ui-map-container">
      <div className="a2ui-card-header">
        <div className="a2ui-badge-icon">
          <MapPin size={16} className="text-nypl-red" />
        </div>
        <div>
          <h4 className="a2ui-card-title">{data.title}</h4>
          <p className="a2ui-card-subtitle">{markers.length} location{markers.length === 1 ? '' : 's'} plotted across NYC</p>
        </div>
      </div>
      <div className="a2ui-map-wrapper" style={{ height: '300px', width: '100%', borderRadius: '8px', overflow: 'hidden' }}>
        <MapContainer
          center={[centerLat, centerLng]}
          zoom={zoom}
          scrollWheelZoom={false}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap'
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          />
          {markers.map((marker, idx) => (
            <Marker
              key={marker.id || idx}
              position={[marker.lat, marker.lng]}
              icon={createCustomPin(marker.category)}
            >
              <Popup className="nypl-map-popup">
                <div className="p-1">
                  <div style={{ fontWeight: 600, fontSize: '13px', color: '#18181B', marginBottom: '2px' }}>
                    {marker.title}
                  </div>
                  {marker.description && (
                    <div style={{ fontSize: '11px', color: '#52525B', marginBottom: '6px' }}>
                      {marker.description}
                    </div>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', color: '#71717A' }}>
                    <Navigation size={10} />
                    <span>{marker.lat.toFixed(4)}, {marker.lng.toFixed(4)}</span>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
};
