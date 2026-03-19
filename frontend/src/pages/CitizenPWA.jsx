import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import VehicleTypeFilter from '../components/citizen/VehicleTypeFilter';

function CitizenPWA() {
    const navigate = useNavigate();
    const { role } = useAuth();
    const [parkingZones, setParkingZones] = useState([]);
    const [vehicleType, setVehicleType] = useState('4w_midsize');

    useEffect(() => {
        // Load some data for citizen view
        const loadCitizenData = async () => {
            try {
                const res = await api.get('/parking/zones');
                if (res.data) setParkingZones(res.data);
            } catch (e) { console.error('Citizen map error', e) }
        };
        loadCitizenData();
        // Simulating a real map PWA here...
    }, []);

    // Mobile app styling for the container
    return (
        <div style={{
            backgroundColor: '#0f172a',
            minHeight: '100vh',
            color: '#fff',
            fontFamily: 'Inter, sans-serif',
            display: 'flex',
            flexDirection: 'column',
            maxWidth: '480px', // Mobile simulation
            margin: '0 auto',
            borderLeft: '1px solid #334155',
            borderRight: '1px solid #334155',
            boxShadow: '0 0 20px rgba(0,0,0,0.5)'
        }}>
            {/* Header / App Bar */}
            <div style={{
                padding: '20px 20px 15px',
                background: 'linear-gradient(to right, #3b82f6, #0ea5e9)',
                color: 'white',
                borderBottomLeftRadius: '24px',
                borderBottomRightRadius: '24px',
                boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <div>
                    <h1 style={{ fontSize: '24px', margin: '0 0 4px 0', fontWeight: 'bold' }}>UrbanFlow</h1>
                    <p style={{ margin: 0, fontSize: '12px', opacity: 0.9 }}>Citizen Connect • Solapur</p>
                </div>
                <button
                    onClick={() => navigate('/')}
                    style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: '#fff', padding: '8px 12px', borderRadius: '16px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}
                >
                    Log Out
                </button>
            </div>

            {/* Main Content Area */}
            <div style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column', gap: '24px' }}>

                {/* Greeting */}
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                    <h2 style={{ fontSize: '20px', margin: 0, color: '#f8fafc' }}>Good Evening, Citizen</h2>
                    <p style={{ fontSize: '14px', color: '#94a3b8', margin: '4px 0 0 0' }}>Plan your commute and find parking.</p>
                </motion.div>

                {/* Quick Actions Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <motion.div onClick={() => navigate('/parking')} whileTap={{ scale: 0.95 }} style={{ backgroundColor: '#1e293b', borderRadius: '16px', padding: '16px', border: '1px solid #334155', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <div style={{ fontSize: '32px' }}>🅿️</div>
                        <span style={{ fontSize: '13px', fontWeight: '600' }}>Find Parking</span>
                    </motion.div>
                    <motion.div onClick={() => navigate('/dashboard')} whileTap={{ scale: 0.95 }} style={{ backgroundColor: '#1e293b', borderRadius: '16px', padding: '16px', border: '1px solid #334155', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <div style={{ fontSize: '32px' }}>🚦</div>
                        <span style={{ fontSize: '13px', fontWeight: '600' }}>Live Traffic</span>
                    </motion.div>
                    <motion.div onClick={() => alert('Issue reporting feature launching soon.')} whileTap={{ scale: 0.95 }} style={{ backgroundColor: '#1e293b', borderRadius: '16px', padding: '16px', border: '1px solid #3b82f6', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <div style={{ fontSize: '32px' }}>🚨</div>
                        <span style={{ fontSize: '13px', fontWeight: '600', color: '#60a5fa' }}>Report Issue</span>
                    </motion.div>
                    <motion.div onClick={() => alert('Transit info feature launching soon.')} whileTap={{ scale: 0.95 }} style={{ backgroundColor: '#1e293b', borderRadius: '16px', padding: '16px', border: '1px solid #334155', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <div style={{ fontSize: '32px' }}>🚌</div>
                        <span style={{ fontSize: '13px', fontWeight: '600' }}>Transit Info</span>
                    </motion.div>
                </div>

                {/* Vehicle Type Selection (New v2.0) */}
                <div style={{ padding: '0 4px' }}>
                    <h3 style={{ fontSize: '11px', fontWeight: '900', color: '#64748b', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px' }}>What are you driving?</h3>
                    <VehicleTypeFilter selected={vehicleType} onSelect={setVehicleType} />
                </div>

                {/* Nearby Parking Status */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '10px' }}>
                    <h3 style={{ fontSize: '16px', margin: 0, color: '#f8fafc', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>Available Slots</h3>

                    {parkingZones.slice(0, 3).map((zone, idx) => {
                        const avail = zone.available_slots !== undefined ? zone.available_slots : (zone.total_slots - (zone.occupied_slots || 0));
                        const pct = ((zone.total_slots - avail) / zone.total_slots) * 100;
                        let color = '#10b981'; // Green
                        if (pct > 70) color = '#f59e0b'; // Yellow
                        if (pct > 90) color = '#ef4444'; // Red

                        return (
                            <div key={idx} style={{ backgroundColor: '#1e293b', borderRadius: '12px', padding: '16px', border: `1px solid #334155` }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                    <span style={{ fontWeight: 'bold', fontSize: '14px' }}>{zone.name}</span>
                                    <span style={{ background: color + '30', color: color, padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold' }}>
                                        {avail} spots free
                                    </span>
                                </div>
                                <div style={{ width: '100%', height: '6px', backgroundColor: '#334155', borderRadius: '3px', overflow: 'hidden' }}>
                                    <div style={{ width: `${pct}%`, height: '100%', backgroundColor: color }} />
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Bottom Nav */}
            <div style={{
                borderTop: '1px solid #334155',
                padding: '12px 20px',
                display: 'flex',
                justifyContent: 'space-between',
                backgroundColor: '#1e293b',
                position: 'sticky',
                bottom: 0
            }}>
                <div onClick={() => navigate('/citizen')} style={{ cursor: 'pointer', color: '#3b82f6', display: 'flex', flexDirection: 'column', alignItems: 'center', fontSize: '11px', fontWeight: 'bold' }}>
                    <span style={{ fontSize: '20px', marginBottom: '4px' }}>🏠</span> Home
                </div>
                <div onClick={() => navigate('/dashboard')} style={{ cursor: 'pointer', color: '#64748b', display: 'flex', flexDirection: 'column', alignItems: 'center', fontSize: '11px' }}>
                    <span style={{ fontSize: '20px', marginBottom: '4px' }}>🗺️</span> Map
                </div>
                <div onClick={() => navigate('/enforcement')} style={{ cursor: 'pointer', color: '#64748b', display: 'flex', flexDirection: 'column', alignItems: 'center', fontSize: '11px' }}>
                    <span style={{ fontSize: '20px', marginBottom: '4px' }}>🔔</span> Alerts
                </div>
                <div onClick={() => alert('Profile settings placeholder')} style={{ cursor: 'pointer', color: '#64748b', display: 'flex', flexDirection: 'column', alignItems: 'center', fontSize: '11px' }}>
                    <span style={{ fontSize: '20px', marginBottom: '4px' }}>👤</span> Profile
                </div>
            </div>
        </div>
    );
}

export default CitizenPWA;
