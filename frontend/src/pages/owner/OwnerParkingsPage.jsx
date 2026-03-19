import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import WebSocketService from '../../services/websocket';

const OwnerParkingsPage = () => {
    const navigate = useNavigate();
    const { currentUser, switchRole } = useAuth();
    const [zones, setZones] = useState([]);

    useEffect(() => {
        const fetchZones = async () => {
            try {
                const ownerId = currentUser ? currentUser.id : 'OWNER_001';
                const res = await api.get(`/parking/owner/${ownerId}/zones`);
                setZones(res.data);
            } catch (err) {
                console.error(err);
            }
        };
        fetchZones();

        const handleUpdate = (data) => {
            if (data && data.zones) fetchZones(); // refresh lazily to get exact own counts
        };
        WebSocketService.on('parking_update', handleUpdate);
        return () => WebSocketService.off('parking_update', handleUpdate);
    }, [currentUser]);

    return (
        <div style={{ padding: '24px', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
                <div style={{ padding: '20px', borderRadius: '16px', backgroundColor: '#1e293b', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                     <div style={{ display: 'flex', gap: '16px' }}>
                        <button onClick={() => navigate('/owner/my-parkings')} style={{ backgroundColor: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>My Zones</button>
                        <button onClick={() => navigate('/owner/bookings')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Bookings</button>
                        <button onClick={() => navigate('/owner/earnings')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Earnings</button>
                     </div>
                     <div style={{ display: 'flex', gap: '16px' }}>
                        <button onClick={() => navigate('/owner/add-parking')} style={{ backgroundColor: '#10b981', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>+ Add New Zone</button>
                        <button onClick={() => { switchRole('citizen'); navigate('/'); }} style={{ backgroundColor: '#475569', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Logout</button>
                     </div>
                </div>

                <h1 style={{ fontSize: '24px', marginBottom: '24px' }}>My Parking Zones</h1>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                    {zones.length === 0 ? <p style={{ color: '#94a3b8' }}>No zones found. Add one to start earning!</p> : null}
                    
                    {zones.map(z => (
                        <div key={z.id} style={{ backgroundColor: '#1e293b', padding: '20px', borderRadius: '16px', border: '1px solid #334155' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                                <h3 style={{ margin: 0, fontSize: '18px' }}>{z.name}</h3>
                                {z.approved ? (
                                    <span style={{ backgroundColor: '#10b98122', color: '#10b981', padding: '4px 8px', borderRadius: '8px', fontSize: '12px', fontWeight: 'bold' }}>Approved</span>
                                ) : (
                                    <span style={{ backgroundColor: '#f59e0b22', color: '#f59e0b', padding: '4px 8px', borderRadius: '8px', fontSize: '12px', fontWeight: 'bold' }}>Pending Approval</span>
                                )}
                            </div>
                            
                            <p style={{ color: '#94a3b8', fontSize: '13px', margin: '0 0 16px 0', minHeight: '38px' }}>{z.address}</p>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', backgroundColor: '#0f172a', padding: '16px', borderRadius: '12px' }}>
                                <div>
                                    <div style={{ color: '#64748b', fontSize: '12px' }}>Live Slots</div>
                                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: z.available_slots === 0 ? '#ef4444' : '#10b981' }}>
                                        {z.available_slots} <span style={{ fontSize: '14px', color: '#475569' }}>/ {z.total_slots}</span>
                                    </div>
                                </div>
                                <div>
                                    <div style={{ color: '#64748b', fontSize: '12px' }}>Rate</div>
                                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f8fafc' }}>
                                        ₹{z.price_per_hour} <span style={{ fontSize: '14px', color: '#475569' }}>/ hr</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default OwnerParkingsPage;
