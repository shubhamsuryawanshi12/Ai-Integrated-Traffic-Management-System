import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';

// Red map pin icon
const customIcon = L.icon({
    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const LocationPicker = ({ position, setPosition, setAddress }) => {
    useMapEvents({
        click: async (e) => {
            const { lat, lng } = e.latlng;
            setPosition([lat, lng]);
            try {
                const res = await api.get(`/parking/geocode/reverse?lat=${lat}&lng=${lng}`);
                const data = res.data;
                if (data.display_name) {
                    setAddress(data.display_name);
                }
            } catch (err) {
                console.error('Geocoding error', err);
            }
        }
    });

    return position === null ? null : (
        <Marker position={position} icon={customIcon} />
    );
};

const AddParkingPage = () => {
    const navigate = useNavigate();
    const { currentUser } = useAuth();

    const [name, setName] = useState('');
    const [price, setPrice] = useState('');
    const [slots, setSlots] = useState('');
    const [address, setAddress] = useState('');
    const [position, setPosition] = useState(null); // [lat, lng]
    
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!position) {
            alert('Please select a location on the map.');
            return;
        }

        setLoading(true);
        try {
            await api.post('/parking/zones/add', {
                owner_id: currentUser ? currentUser.id : 'OWNER_001',
                name: name,
                address: address,
                latitude: position[0],
                longitude: position[1],
                price_per_hour: parseFloat(price),
                total_slots: parseInt(slots, 10)
            });
            alert('Parking zone submitted for admin approval!');
            navigate('/owner/my-parkings');
        } catch (err) {
            alert('Failed to submit parking zone.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: '24px', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                <button onClick={() => navigate('/owner/my-parkings')} style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', marginBottom: '16px' }}>
                    ← Back to My Parkings
                </button>
                <h1 style={{ fontSize: '24px', marginBottom: '24px', marginTop: 0 }}>Add New Parking Zone</h1>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                    
                    <form onSubmit={handleSubmit} style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '4px' }}>Zone Name</label>
                            <input required type="text" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Downtown Metro Plaza" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #475569', backgroundColor: '#0f172a', color: 'white', boxSizing: 'border-box' }} />
                        </div>
                        
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '4px' }}>Price per Hour (₹)</label>
                                <input required type="number" step="0.5" value={price} onChange={e => setPrice(e.target.value)} placeholder="20" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #475569', backgroundColor: '#0f172a', color: 'white', boxSizing: 'border-box' }} />
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '4px' }}>Total Slots</label>
                                <input required type="number" min="1" value={slots} onChange={e => setSlots(e.target.value)} placeholder="50" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #475569', backgroundColor: '#0f172a', color: 'white', boxSizing: 'border-box' }} />
                            </div>
                        </div>

                        <div>
                            <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '4px' }}>Address (Detected from Map)</label>
                            <textarea required value={address} onChange={e => setAddress(e.target.value)} rows="3" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #475569', backgroundColor: '#0f172a', color: 'white', boxSizing: 'border-box' }} />
                        </div>

                        <button type="submit" disabled={loading} style={{ backgroundColor: '#3b82f6', color: 'white', padding: '16px', borderRadius: '12px', border: 'none', fontWeight: 'bold', fontSize: '16px', cursor: 'pointer', marginTop: '8px' }}>
                            {loading ? 'Submitting...' : 'Submit for Approval'}
                        </button>
                    </form>

                    <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '16px', border: '1px solid #334155' }}>
                        <p style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#94a3b8' }}>Tap anywhere on the map to mark your location.</p>
                        <div style={{ height: '400px', borderRadius: '8px', overflow: 'hidden' }}>
                            <MapContainer center={[17.6868, 75.9060]} zoom={13} style={{ height: '100%', width: '100%' }}>
                                <TileLayer
                                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                />
                                <LocationPicker position={position} setPosition={setPosition} setAddress={setAddress} />
                            </MapContainer>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AddParkingPage;
