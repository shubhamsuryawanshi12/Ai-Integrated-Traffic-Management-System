import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useNavigate } from 'react-router-dom';

// Center map on Solapur
const DEFAULT_CENTER = [17.6868, 75.9060];

const RecenterMap = ({ center }) => {
    const map = useMap();
    useEffect(() => {
        map.setView(center, map.getZoom());
    }, [center, map]);
    return null;
};

const ParkingMap = ({ zones, onZoneSelect, selectedZoneId, userRole }) => {
    const navigate = useNavigate();

    // Determine color based on availability rules
    const createMarkerIcon = (zone, isSelected) => {
        const available = zone.total_slots - zone.occupied_slots;
        const isRed = available === 0;
        const isGreen = available > (zone.total_slots * 0.5);
        const color = isRed ? '#ef4444' : (isGreen ? '#22c55e' : '#fbbf24');
        const border = isSelected ? '3px solid #60a5fa' : '2px solid white';
        const textColor = isRed || isGreen ? 'white' : 'black';

        return L.divIcon({
            className: 'custom-parking-marker',
            html: `
                <div style="background-color: ${color}; width: 32px; height: 32px; border-radius: 50%; border: ${border}; display: flex; align-items: center; justify-content: center; color: ${textColor}; font-weight: bold; font-size: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.5);">
                    ${available}
                </div>
            `,
            iconSize: [32, 32],
            iconAnchor: [16, 16],
        });
    };

    return (
        <div style={{ height: '400px', width: '100%', borderRadius: '12px', overflow: 'hidden', border: '1px solid #334155' }}>
            <MapContainer center={DEFAULT_CENTER} zoom={13} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                />

                {zones.map((zone) => {
                    // Use zone_id or id (for new spec)
                    const zId = zone.zone_id || zone.id;
                    const isSelected = selectedZoneId === zId;
                    
                    return (
                        <Marker
                            key={zId}
                            position={[zone.latitude || zone.lat, zone.longitude || zone.lng]}
                            icon={createMarkerIcon(zone, isSelected)}
                            eventHandlers={{
                                click: () => {
                                    if (userRole === 'driver' || userRole === 'citizen') {
                                        navigate(`/parking/${zId}`);
                                    } else if (onZoneSelect) {
                                        onZoneSelect(zone);
                                    }
                                }
                            }}
                        >
                            <Tooltip direction="top" offset={[0, -10]} opacity={1}>
                                <strong>{zone.name}</strong><br />
                                {zone.total_slots - zone.occupied_slots} slots available
                            </Tooltip>
                        </Marker>
                    );
                })}
            </MapContainer>
        </div>
    );
};

export default ParkingMap;
