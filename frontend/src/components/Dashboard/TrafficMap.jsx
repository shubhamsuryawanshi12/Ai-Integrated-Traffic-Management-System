import React, { useEffect, useState, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom traffic light icons
const createTrafficLightIcon = (color) => {
    return L.divIcon({
        className: 'custom-traffic-icon',
        html: `
      <div style="
        width: 24px;
        height: 24px;
        background-color: ${color};
        border: 3px solid #333;
        border-radius: 50%;
        box-shadow: 0 0 10px ${color}, 0 0 20px ${color};
        position: relative;
      ">
        <div style="
          position: absolute;
          width: 12px;
          height: 12px;
          background-color: white;
          border-radius: 50%;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          opacity: 0.3;
        "></div>
      </div>
    `,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
    });
};

// User location marker icon
const userLocationIcon = L.divIcon({
    className: 'user-location-icon',
    html: `
    <div style="
      width: 20px;
      height: 20px;
      background-color: #3b82f6;
      border: 3px solid #fff;
      border-radius: 50%;
      box-shadow: 0 0 15px #3b82f6, 0 0 30px rgba(59, 130, 246, 0.5);
      position: relative;
    ">
      <div style="
        position: absolute;
        width: 40px;
        height: 40px;
        background-color: rgba(59, 130, 246, 0.2);
        border-radius: 50%;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        animation: pulse-ring 2s infinite;
      "></div>
    </div>
  `,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
});

// Generate intersections around a given location
const generateIntersectionsAroundLocation = (lat, lng) => {
    const gridSize = 3;
    const spacing = 0.003; // roughly 300 meters
    const intersections = [];
    const statuses = ['red', 'yellow', 'green'];
    const streetNames = [
        'Main St', 'Oak Ave', 'Park Rd', 'Market St', 'Station Rd',
        'Church St', 'School Ln', 'Temple Rd', 'Gandhi Marg', 'Nehru Rd'
    ];

    for (let i = 0; i < gridSize; i++) {
        for (let j = 0; j < gridSize; j++) {
            const id = `intersection-${i}-${j}`;
            const intLat = lat + (i - 1) * spacing;
            const intLng = lng + (j - 1) * spacing;
            const status = statuses[Math.floor(Math.random() * statuses.length)];
            const queueLength = Math.floor(Math.random() * 15);
            const throughput = Math.floor(Math.random() * 50) + 10;

            intersections.push({
                id,
                position: [intLat, intLng],
                status,
                queueLength,
                throughput,
                name: `${streetNames[(i * 3 + j) % streetNames.length]} & Cross ${j + 1}`,
            });
        }
    }

    return intersections;
};

// Component to update map view and handle location
const MapController = ({ center, userLocation, onRecenter }) => {
    const map = useMap();

    useEffect(() => {
        if (center) {
            map.flyTo(center, 15, { duration: 1.5 });
        }
    }, [center, map]);

    return null;
};

const TrafficMap = ({ intersections: propIntersections, style }) => {
    const [intersections, setIntersections] = useState([]);
    const [center, setCenter] = useState([20.5937, 78.9629]); // Default: India center
    const [userLocation, setUserLocation] = useState(null);
    const [locationError, setLocationError] = useState(null);
    const [isLocating, setIsLocating] = useState(true);
    const [locationName, setLocationName] = useState('Detecting location...');

    // Get user's current location
    const getCurrentLocation = useCallback(() => {
        setIsLocating(true);
        setLocationError(null);

        if (!navigator.geolocation) {
            setLocationError('Geolocation not supported');
            setIsLocating(false);
            // Fallback to default location
            const defaultLat = 28.6139; // Delhi
            const defaultLng = 77.2090;
            setCenter([defaultLat, defaultLng]);
            setUserLocation([defaultLat, defaultLng]);
            setIntersections(generateIntersectionsAroundLocation(defaultLat, defaultLng));
            setLocationName('Delhi, India (Default)');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;
                console.log('📍 Location obtained:', latitude, longitude);

                setUserLocation([latitude, longitude]);
                setCenter([latitude, longitude]);
                setIntersections(generateIntersectionsAroundLocation(latitude, longitude));
                setIsLocating(false);

                // Reverse geocode to get location name
                try {
                    const response = await fetch(
                        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`
                    );
                    const data = await response.json();
                    const address = data.address;
                    const name = address.suburb || address.neighbourhood || address.city || address.town || address.village || 'Your Location';
                    setLocationName(`${name}, ${address.state || address.country || ''}`);
                } catch (error) {
                    setLocationName('Your Current Location');
                }
            },
            (error) => {
                console.error('Location error:', error);
                setLocationError(error.message);
                setIsLocating(false);

                // Fallback to Delhi, India
                const defaultLat = 28.6139;
                const defaultLng = 77.2090;
                setCenter([defaultLat, defaultLng]);
                setUserLocation([defaultLat, defaultLng]);
                setIntersections(generateIntersectionsAroundLocation(defaultLat, defaultLng));
                setLocationName('Delhi, India (Default)');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }, []);

    // Get location on mount
    useEffect(() => {
        getCurrentLocation();
    }, [getCurrentLocation]);

    // Use provided intersections if available
    useEffect(() => {
        if (propIntersections && propIntersections.length > 0) {
            setIntersections(propIntersections);
        }
    }, [propIntersections]);

    // Simulate traffic light changes
    useEffect(() => {
        const interval = setInterval(() => {
            setIntersections(prevIntersections =>
                prevIntersections.map(intersection => ({
                    ...intersection,
                    status: ['red', 'yellow', 'green'][Math.floor(Math.random() * 3)],
                    queueLength: Math.floor(Math.random() * 15),
                    throughput: Math.floor(Math.random() * 50) + 10,
                }))
            );
        }, 3000);

        return () => clearInterval(interval);
    }, []);

    const getColorForStatus = (status) => {
        switch (status) {
            case 'red': return '#ef4444';
            case 'yellow': return '#fbbf24';
            case 'green': return '#22c55e';
            default: return '#6b7280';
        }
    };

    return (
        <div style={{ height: '100%', width: '100%', position: 'relative', minHeight: '450px', ...style }}>
            <MapContainer
                center={center}
                zoom={15}
                style={{ height: '100%', width: '100%', borderRadius: '8px', minHeight: '450px' }}
                zoomControl={true}
            >
                {/* Dark theme map tiles */}
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />

                <MapController center={center} userLocation={userLocation} />

                {/* User's current location marker */}
                {userLocation && (
                    <Marker position={userLocation} icon={userLocationIcon}>
                        <Popup>
                            <div style={{ color: '#000', textAlign: 'center' }}>
                                <h3 style={{ margin: '0 0 8px 0', fontSize: '14px', fontWeight: 'bold', color: '#3b82f6' }}>
                                    📍 You are here
                                </h3>
                                <p style={{ margin: '0', fontSize: '12px' }}>
                                    {locationName}
                                </p>
                                <p style={{ margin: '4px 0 0 0', fontSize: '10px', color: '#666' }}>
                                    {userLocation[0].toFixed(4)}, {userLocation[1].toFixed(4)}
                                </p>
                            </div>
                        </Popup>
                    </Marker>
                )}

                {/* Render intersections */}
                {intersections.map((intersection) => (
                    <React.Fragment key={intersection.id}>
                        <Marker
                            position={intersection.position}
                            icon={createTrafficLightIcon(getColorForStatus(intersection.status))}
                        >
                            <Popup>
                                <div style={{ color: '#000' }}>
                                    <h3 style={{ margin: '0 0 8px 0', fontSize: '14px', fontWeight: 'bold' }}>
                                        🚦 {intersection.name}
                                    </h3>
                                    <p style={{ margin: '4px 0', fontSize: '12px' }}>
                                        <strong>Status:</strong>{' '}
                                        <span style={{ color: getColorForStatus(intersection.status), fontWeight: 'bold' }}>
                                            {intersection.status.toUpperCase()}
                                        </span>
                                    </p>
                                    <p style={{ margin: '4px 0', fontSize: '12px' }}>
                                        <strong>Queue:</strong> {intersection.queueLength} vehicles
                                    </p>
                                    <p style={{ margin: '4px 0', fontSize: '12px' }}>
                                        <strong>Throughput:</strong> {intersection.throughput} veh/min
                                    </p>
                                </div>
                            </Popup>
                        </Marker>

                        <Circle
                            center={intersection.position}
                            radius={50}
                            pathOptions={{
                                color: getColorForStatus(intersection.status),
                                fillColor: getColorForStatus(intersection.status),
                                fillOpacity: 0.15,
                                weight: 2,
                            }}
                        />
                    </React.Fragment>
                ))}
            </MapContainer>

            {/* Location Info Box */}
            <div style={{
                position: 'absolute',
                top: '12px',
                left: '12px',
                backgroundColor: 'rgba(0, 0, 0, 0.85)',
                padding: '12px 16px',
                borderRadius: '8px',
                zIndex: 1000,
                border: '1px solid rgba(255, 255, 255, 0.1)',
                maxWidth: '250px',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <div style={{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        backgroundColor: '#3b82f6',
                        boxShadow: '0 0 8px #3b82f6',
                        animation: 'pulse 2s infinite',
                    }}></div>
                    <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#fff' }}>
                        {isLocating ? 'Detecting...' : 'YOUR LOCATION'}
                    </span>
                </div>
                <p style={{ margin: '0', fontSize: '13px', color: '#94a3b8' }}>
                    {locationName}
                </p>
                {locationError && (
                    <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: '#f59e0b' }}>
                        ⚠️ {locationError}
                    </p>
                )}
            </div>

            {/* Recenter Button */}
            <button
                onClick={getCurrentLocation}
                disabled={isLocating}
                style={{
                    position: 'absolute',
                    top: '12px',
                    right: '60px',
                    backgroundColor: 'rgba(0, 0, 0, 0.85)',
                    color: '#fff',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    cursor: isLocating ? 'wait' : 'pointer',
                    zIndex: 1000,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                }}
            >
                {isLocating ? '⏳' : '📍'} {isLocating ? 'Locating...' : 'My Location'}
            </button>

            {/* Legend */}
            <div style={{
                position: 'absolute',
                bottom: '20px',
                right: '20px',
                backgroundColor: 'rgba(0, 0, 0, 0.85)',
                padding: '12px',
                borderRadius: '8px',
                zIndex: 1000,
                border: '1px solid rgba(255, 255, 255, 0.1)',
            }}>
                <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '8px', color: '#fff' }}>
                    Traffic Signals
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                            width: '14px', height: '14px', borderRadius: '50%',
                            backgroundColor: '#22c55e', boxShadow: '0 0 6px #22c55e',
                        }}></div>
                        <span style={{ fontSize: '11px', color: '#fff' }}>Green - Go</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                            width: '14px', height: '14px', borderRadius: '50%',
                            backgroundColor: '#fbbf24', boxShadow: '0 0 6px #fbbf24',
                        }}></div>
                        <span style={{ fontSize: '11px', color: '#fff' }}>Yellow - Caution</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                            width: '14px', height: '14px', borderRadius: '50%',
                            backgroundColor: '#ef4444', boxShadow: '0 0 6px #ef4444',
                        }}></div>
                        <span style={{ fontSize: '11px', color: '#fff' }}>Red - Stop</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px', paddingTop: '6px', borderTop: '1px solid #333' }}>
                        <div style={{
                            width: '14px', height: '14px', borderRadius: '50%',
                            backgroundColor: '#3b82f6', border: '2px solid #fff',
                        }}></div>
                        <span style={{ fontSize: '11px', color: '#fff' }}>Your Location</span>
                    </div>
                </div>
            </div>

            {/* Live indicator */}
            <div style={{
                position: 'absolute',
                bottom: '20px',
                left: '12px',
                backgroundColor: 'rgba(0, 0, 0, 0.85)',
                padding: '8px 12px',
                borderRadius: '8px',
                zIndex: 1000,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
            }}>
                <div style={{
                    width: '8px', height: '8px', borderRadius: '50%',
                    backgroundColor: '#22c55e', boxShadow: '0 0 8px #22c55e',
                    animation: 'pulse 2s infinite',
                }}></div>
                <span style={{ fontSize: '11px', color: '#fff', fontWeight: 'bold' }}>
                    LIVE TRAFFIC • {intersections.length} Intersections
                </span>
            </div>

            <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.2); }
        }
        @keyframes pulse-ring {
          0% { transform: translate(-50%, -50%) scale(0.5); opacity: 1; }
          100% { transform: translate(-50%, -50%) scale(2); opacity: 0; }
        }
        .custom-traffic-icon, .user-location-icon {
          background: transparent !important;
          border: none !important;
        }
      `}</style>
        </div>
    );
};

export default TrafficMap;
