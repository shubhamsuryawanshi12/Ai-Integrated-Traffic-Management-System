import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import WebSocketService from '../../services/websocket';
import { useAuth } from '../../context/AuthContext';
import { motion } from 'framer-motion';

const ParkingDetailPage = () => {
    const { zoneId } = useParams();
    const navigate = useNavigate();
    const { currentUser } = useAuth();
    
    const [zone, setZone] = useState(null);
    const [prediction, setPrediction] = useState(null);
    
    // Default times (now + 1 hour)
    const [startTime, setStartTime] = useState(() => {
        const d = new Date();
        d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
        return d.toISOString().slice(0, 16);
    });
    const [endTime, setEndTime] = useState(() => {
        const d = new Date();
        d.setHours(d.getHours() + 1);
        d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
        return d.toISOString().slice(0, 16);
    });

    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Fetch zone details
        const fetchZone = async () => {
            try {
                const res = await api.get(`/parking/zones/${zoneId}`);
                setZone(res.data);
            } catch (err) {
                console.error('Failed to fetch zone details', err);
            }
        };
        
        // Fetch prediction
        const fetchPrediction = async () => {
            try {
                const hour = new Date().getHours() + 1; // predict next hour
                const res = await api.get(`/parking/predict/${zoneId}?hour=${hour}`);
                setPrediction(res.data.predicted_occupancy_percent);
            } catch (err) {
                console.error('Failed to fetch prediction', err);
            }
        };

        fetchZone();
        fetchPrediction();

        // WebSocket for live slot updates
        const handleParkingUpdate = (data) => {
            if (data && data.zones) {
                const updatedZone = data.zones.find(z => z.id === zoneId || z.zone_id === zoneId);
                if (updatedZone) {
                    setZone(prev => ({ ...prev, available_slots: updatedZone.available_slots || updatedZone.available_slots === 0 ? updatedZone.available_slots : (updatedZone.total_slots - updatedZone.occupied_slots) }));
                }
            }
        };

        WebSocketService.on('parking_update', handleParkingUpdate);
        return () => {
            WebSocketService.off('parking_update', handleParkingUpdate);
        };
    }, [zoneId]);

    if (!zone) return <div style={{ color: 'white', padding: '20px' }}>Loading...</div>;

    // Calculate Amount
    const start = new Date(startTime);
    const end = new Date(endTime);
    const diffMs = end - start;
    const diffHours = diffMs / (1000 * 60 * 60);
    const totalAmount = diffHours > 0 ? (diffHours * zone.price_per_hour).toFixed(2) : 0;

    const handleBookNow = async () => {
        setError('');
        if (diffHours <= 0) {
            setError('End time must be after start time.');
            return;
        }
        if (zone.available_slots <= 0) {
            setError('No slots available.');
            return;
        }
        
        setLoading(true);
        try {
            const res = await api.post('/parking/book', {
                user_id: currentUser ? currentUser.id : 'DRIVER_001',
                parking_id: zoneId,
                start_time: start.toISOString(),
                end_time: end.toISOString()
            });
            if (res.data.success) {
                navigate(`/parking/booking/${res.data.booking_id}/confirm`);
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to book slot.');
        } finally {
            setLoading(false);
        }
    };

    const isFull = zone.available_slots <= 0;
    const availableColor = isFull ? '#ef4444' : (zone.available_slots > zone.total_slots * 0.5 ? '#22c55e' : '#fbbf24');

    return (
        <div style={{ padding: '24px', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ maxWidth: '600px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <button onClick={() => navigate(-1)} style={{ alignSelf: 'flex-start', background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '14px', marginBottom: '8px' }}>
                    ← Back to Map
                </button>

                {/* Info Card */}
                <div style={{ backgroundColor: '#1e293b', borderRadius: '16px', padding: '24px', border: '1px solid #334155' }}>
                    <h1 style={{ margin: '0 0 8px 0', fontSize: '24px' }}>{zone.name}</h1>
                    <p style={{ margin: 0, color: '#94a3b8', fontSize: '14px' }}>{zone.address}</p>
                    <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                        <span style={{ backgroundColor: '#334155', padding: '4px 12px', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold' }}>{zone.type?.toUpperCase()}</span>
                        <span style={{ backgroundColor: '#3b82f633', color: '#60a5fa', padding: '4px 12px', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold' }}>₹{zone.price_per_hour}/hr</span>
                    </div>
                </div>

                {/* Live Slot Counter */}
                <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} style={{ backgroundColor: '#1e293b', borderRadius: '16px', padding: '24px', border: `2px solid ${availableColor}44`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h3 style={{ margin: '0 0 4px 0', color: '#94a3b8', fontSize: '14px' }}>Live Availability</h3>
                        <p style={{ margin: 0, color: availableColor, fontWeight: 'bold' }}>{isFull ? 'Zone Full' : 'Spots Available'}</p>
                    </div>
                    <div style={{ fontSize: '48px', fontWeight: 'bold', color: availableColor }}>
                        {zone.available_slots} <span style={{ fontSize: '24px', color: '#64748b' }}>/ {zone.total_slots}</span>
                    </div>
                </motion.div>

                {/* Prediction Strip */}
                {prediction !== null && (
                    <div style={{ backgroundColor: '#8b5cf633', border: '1px solid #8b5cf6', borderRadius: '12px', padding: '12px 16px', color: '#c4b5fd', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>🔮</span>
                        <span>Predicted occupancy next hour: <strong>{Math.round(prediction * 100)}%</strong></span>
                    </div>
                )}

                {/* Time Picker Component */}
                <div style={{ backgroundColor: '#1e293b', borderRadius: '16px', padding: '24px', border: '1px solid #334155' }}>
                    <h3 style={{ margin: '0 0 16px 0', fontSize: '16px' }}>Select Duration</h3>
                    <div style={{ display: 'flex', gap: '16px' }}>
                        <div style={{ flex: 1 }}>
                            <label style={{ display: 'block', marginBottom: '8px', fontSize: '12px', color: '#94a3b8' }}>Entry Time</label>
                            <input 
                                type="datetime-local" 
                                value={startTime} 
                                onChange={(e) => setStartTime(e.target.value)}
                                style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #475569', backgroundColor: '#0f172a', color: 'white', boxSizing: 'border-box' }}
                            />
                        </div>
                        <div style={{ flex: 1 }}>
                            <label style={{ display: 'block', marginBottom: '8px', fontSize: '12px', color: '#94a3b8' }}>Exit Time</label>
                            <input 
                                type="datetime-local" 
                                value={endTime} 
                                onChange={(e) => setEndTime(e.target.value)}
                                style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #475569', backgroundColor: '#0f172a', color: 'white', boxSizing: 'border-box' }}
                            />
                        </div>
                    </div>

                    {/* Cost Calculation */}
                    <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px dashed #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                            <div style={{ color: '#94a3b8', fontSize: '12px' }}>Total Amount</div>
                            <div style={{ fontSize: '12px' }}>{diffHours > 0 ? `${diffHours.toFixed(1)} hrs @ ₹${zone.price_per_hour}/hr` : '--'}</div>
                        </div>
                        <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff' }}>
                            ₹{totalAmount}
                        </div>
                    </div>
                </div>

                {error && <div style={{ color: '#ef4444', backgroundColor: '#ef444422', padding: '12px', borderRadius: '8px', fontSize: '14px', textAlign: 'center' }}>{error}</div>}

                <button 
                    onClick={handleBookNow} 
                    disabled={isFull || loading || diffHours <= 0}
                    style={{ 
                        width: '100%', backgroundColor: isFull || diffHours <= 0 ? '#475569' : '#3b82f6', 
                        color: isFull || diffHours <= 0 ? '#94a3b8' : 'white', 
                        padding: '16px', borderRadius: '12px', fontWeight: 'bold', fontSize: '16px', border: 'none', 
                        cursor: isFull || diffHours <= 0 ? 'not-allowed' : 'pointer', transition: 'background-color 0.2s',
                        marginTop: '8px'
                    }}
                >
                    {loading ? 'Processing...' : (isFull ? 'No Slots Available' : 'Book Now')}
                </button>
            </div>
        </div>
    );
};

export default ParkingDetailPage;
