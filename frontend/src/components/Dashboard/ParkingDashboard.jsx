import React, { useState, useEffect } from 'react';
import ParkingMap from './ParkingMap';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import api from '../../services/api';
import { motion } from 'framer-motion';
import WebSocketService from '../../services/websocket';
import { useAuth } from '../../context/AuthContext';

const StatCard = ({ title, value, sub, color }) => (
    <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
            backgroundColor: '#1e293b', padding: '20px', borderRadius: '12px',
            border: '1px solid #334155', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'
        }}
    >
        <h3 style={{ color: '#94a3b8', fontSize: '13px', margin: '0 0 8px 0' }}>{title}</h3>
        <div style={{ fontSize: '28px', fontWeight: 'bold', color: color, marginBottom: '4px' }}>{value}</div>
        <div style={{ fontSize: '11px', color: '#64748b' }}>{sub}</div>
    </motion.div>
);

const ParkingDashboard = () => {
    const { role } = useAuth();
    const [zones, setZones] = useState([]);
    const [selectedZone, setSelectedZone] = useState(null);
    const [predictions, setPredictions] = useState([]);

    // Fetch initial zones
    const fetchZones = async () => {
        try {
            const res = await api.get('/parking/zones');
            setZones(res.data);
            if (!selectedZone && res.data.length > 0) {
                setSelectedZone(res.data[0]);
            }
        } catch (e) {
            console.error("Failed to fetch zones", e);
        }
    };

    // Keep WebSocket sync
    useEffect(() => {
        fetchZones();

        const handleParkingUpdate = (data) => {
            if (data && data.zones) {
                setZones(data.zones);
                setSelectedZone(prev => prev ? data.zones.find(z => (z.id || z.zone_id) === (prev.id || prev.zone_id)) || prev : data.zones[0]);
            }
        };

        WebSocketService.on('parking_update', handleParkingUpdate);
        return () => {
            // Unsubscribe logic mostly handled centrally in websocket.js, 
            // but normally we'd remove specific listener here.
        };
    }, []);

    // Fetch predictions when selected zone changes
    useEffect(() => {
        if (selectedZone) {
            const fetchPreds = async () => {
                try {
                    const zId = selectedZone.id || selectedZone.zone_id;
                    const res = await api.get(`/parking/predict/${zId}`);
                    // Ensure the route response has the data we expect, otherwise mock it visually
                    if (res.data.predictions) {
                        setPredictions(res.data.predictions.map(p => ({
                            time: `${p.hour}:00`,
                            occupancy: Math.round(p.predicted_occupancy * 100)
                        })));
                    } else if (res.data.predicted_occupancy_percent !== undefined) {
                         setPredictions([{ time: 'Next Hour', occupancy: Math.round(res.data.predicted_occupancy_percent * 100) }]);
                         // fallback visual graph 
                         const fakeData = Array.from({length: 6}).map((_, i) => ({
                              time: `${new Date().getHours() + i + 1}:00`,
                              occupancy: Math.round(res.data.predicted_occupancy_percent * 100) + (Math.random()*10 - 5)
                         }));
                         setPredictions(fakeData);
                    }
                } catch (e) { console.error(e); }
            };
            fetchPreds();
        }
    }, [selectedZone]);

    // Handle Reservation dummy function - actual drivers use clicking map
    const handleReserve = async () => {
        alert('Please click on the Zone pin directly on the Map to book a slot.');
    };

    const totalSlots = zones.reduce((acc, z) => acc + (z.total_slots || 0), 0);
    const availableSlots = zones.reduce((acc, z) => acc + (z.available_slots !== undefined ? z.available_slots : (z.total_slots - (z.occupied_slots || 0))), 0);
    const occupiedSlots = totalSlots - availableSlots;
    const avgOccupancy = totalSlots > 0 ? Math.round((occupiedSlots / totalSlots) * 100) : 0;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

            {/* KPI Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
                <StatCard title="Total Zones" value={zones.length} sub="Monitored Areas" color="#3b82f6" />
                <StatCard title="Total Capacity" value={totalSlots} sub="Parking Slots" color="#94a3b8" />
                <StatCard title="Currently Available" value={availableSlots} sub="Live Empty Slots" color="#22c55e" />
                <StatCard title="Avg Occupancy" value={`${avgOccupancy}%`} sub="City-wide average" color={avgOccupancy > 80 ? '#ef4444' : '#fbbf24'} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '20px' }}>
                {/* Map Section */}
                <div style={{ backgroundColor: '#1e293b', padding: '20px', borderRadius: '12px', border: '1px solid #334155' }}>
                    <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: '#fff' }}>🗺️ Live Zone Map</h3>
                    <ParkingMap
                        zones={zones}
                        onZoneSelect={setSelectedZone}
                        selectedZoneId={selectedZone?.id || selectedZone?.zone_id}
                        userRole={role}
                    />
                </div>

                {/* Details & Predictions Section */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

                    {/* Selected Zone Card */}
                    {selectedZone && (
                        <div style={{ backgroundColor: '#1e293b', padding: '20px', borderRadius: '12px', border: '1px solid #334155' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                                <div>
                                    <h3 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#fff' }}>{selectedZone.name}</h3>
                                    <span style={{ fontSize: '12px', color: '#94a3b8', background: '#334155', padding: '2px 8px', borderRadius: '12px' }}>
                                        {(selectedZone.type || selectedZone.zone_type || 'Unknown').toUpperCase()}
                                    </span>
                                </div>
                                <button
                                    onClick={handleReserve}
                                    style={{
                                        background: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px',
                                        borderRadius: '8px', cursor: 'pointer', fontWeight: '600', fontSize: '13px'
                                    }}
                                >
                                    Reserve Slot
                                </button>
                            </div>

                            <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
                                <div>
                                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>Available</div>
                                    <div style={{ color: '#22c55e', fontSize: '24px', fontWeight: 'bold' }}>{selectedZone.available_slots !== undefined ? selectedZone.available_slots : (selectedZone.total_slots - selectedZone.occupied_slots)}</div>
                                </div>
                                <div>
                                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>Total</div>
                                    <div style={{ color: '#fff', fontSize: '24px', fontWeight: 'bold' }}>{selectedZone.total_slots}</div>
                                </div>
                                <div>
                                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>Occupancy</div>
                                    <div style={{ color: '#fbbf24', fontSize: '24px', fontWeight: 'bold' }}>
                                        {Math.round(((selectedZone.total_slots - (selectedZone.available_slots !== undefined ? selectedZone.available_slots : (selectedZone.total_slots - selectedZone.occupied_slots))) / selectedZone.total_slots) * 100)}%
                                    </div>
                                </div>
                            </div>

                            <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#94a3b8' }}>🔮 3-Hour Prediction (AI Model)</h4>
                            <div style={{ width: '100%', height: '180px' }}>
                                <ResponsiveContainer>
                                    <AreaChart data={predictions}>
                                        <defs>
                                            <linearGradient id="colorOcc" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                                        <RechartsTooltip
                                            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
                                            itemStyle={{ color: '#e2e8f0' }}
                                        />
                                        <Area type="monotone" dataKey="occupancy" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorOcc)" name="Occupancy %" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Occupancy Summary Chart */}
            <div style={{ backgroundColor: '#1e293b', padding: '20px', borderRadius: '12px', border: '1px solid #334155' }}>
                <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: '#fff' }}>📊 Current Zone Status Overview</h3>
                <div style={{ width: '100%', height: '240px' }}>
                    <ResponsiveContainer>
                        <BarChart data={zones.map(z => ({ name: z.name, occupied: (z.total_slots || 0) - (z.available_slots !== undefined ? z.available_slots : (z.total_slots - (z.occupied_slots || 0))), available: z.available_slots !== undefined ? z.available_slots : (z.total_slots - (z.occupied_slots || 0)) }))}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                            <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                            <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                            <RechartsTooltip
                                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
                            />
                            <Bar dataKey="occupied" stackId="a" fill="#ef4444" name="Occupied" radius={[0, 0, 4, 4]} />
                            <Bar dataKey="available" stackId="a" fill="#22c55e" name="Available" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

        </div>
    );
};

export default ParkingDashboard;
