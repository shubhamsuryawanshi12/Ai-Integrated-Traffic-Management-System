import React from 'react';
import { motion } from 'framer-motion';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar
} from 'recharts';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

// Initial Mock Data Fallback
const INIT_WAIT_TIME_DATA = [
    { time: '08:00', baseline: 120, ai: 45 },
    { time: '09:00', baseline: 180, ai: 60 },
];

const EMISSIONS_DATA = [
    { day: 'Mon', saved: 120 },
    { day: 'Tue', saved: 145 },
    { day: 'Wed', saved: 132 },
    { day: 'Thu', saved: 150 },
    { day: 'Fri', saved: 180 },
    { day: 'Sat', saved: 90 },
    { day: 'Sun', saved: 85 },
];

const KPICard = ({ title, value, sub, color }) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{
            backgroundColor: '#1e293b',
            padding: '24px',
            borderRadius: '16px',
            border: '1px solid #334155',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
        }}
    >
        <h3 style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px', marginTop: 0 }}>{title}</h3>
        <div style={{ fontSize: '32px', fontWeight: 'bold', color: color, marginBottom: '4px' }}>{value}</div>
        <div style={{ fontSize: '12px', color: '#64748b' }}>{sub}</div>
    </motion.div>
);

const ChartCard = ({ title, children }) => (
    <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        style={{
            backgroundColor: '#1e293b',
            padding: '24px',
            borderRadius: '16px',
            border: '1px solid #334155'
        }}
    >
        <h3 style={{ color: '#fff', fontSize: '18px', marginBottom: '24px', marginTop: 0 }}>{title}</h3>
        <div style={{ width: '100%', height: '300px' }}>
            {children}
        </div>
    </motion.div>
);

const Analytics = () => {
    const navigate = useNavigate();
    const [waitTimeData, setWaitTimeData] = React.useState(INIT_WAIT_TIME_DATA);
    const [emissionsData, setEmissionsData] = React.useState(EMISSIONS_DATA);

    React.useEffect(() => {
        const fetchPredictions = async () => {
            try {
                const res = await api.get('/prediction/forecast');
                if (res.data && res.data.forecast) {
                    const mapped = res.data.forecast.map(item => ({
                        time: item.time,
                        baseline: item.baseline_wait_sec,
                        ai: item.ai_wait_sec,
                        volume: item.predicted_volume
                    }));
                    setWaitTimeData(mapped);
                }
            } catch (e) { console.error('Error fetching traffic forecast:', e); }
        };
        fetchPredictions();
    }, []);


    return (
        <div style={{
            backgroundColor: '#0f172a',
            minHeight: '100vh',
            color: '#fff',
            padding: '40px',
            fontFamily: 'Inter, sans-serif'
        }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
                <div>
                    <h1 style={{
                        fontSize: '36px',
                        fontWeight: 'bold',
                        margin: 0,
                        background: 'linear-gradient(to right, #3b82f6, #06b6d4)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        marginBottom: '10px'
                    }}>
                        Performance Analytics
                    </h1>
                    <p style={{ color: '#94a3b8', margin: 0 }}>Historical analysis of AI Efficiency vs. Traditional Control</p>
                </div>
                <button
                    onClick={() => navigate('/dashboard')}
                    style={{
                        padding: '12px 24px',
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '8px',
                        color: '#fff',
                        cursor: 'pointer',
                        fontWeight: '600',
                        fontSize: '14px',
                        transition: 'all 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#334155'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#1e293b'}
                >
                    <span>←</span> Back to Dashboard
                </button>
            </div>

            {/* KPI Cards */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                gap: '24px',
                marginBottom: '40px'
            }}>
                <KPICard title="Avg Wait Time Reduction" value="-58%" sub="Compared to fixed timing" color="#22c55e" />
                <KPICard title="Total CO₂ Saved" value="1,240 kg" sub="This week alone" color="#3b82f6" />
                <KPICard title="Traffic Flow Efficiency" value="+34%" sub="Throughput increase" color="#f59e0b" />
                <KPICard title="Emergency Response" value="-2.5 min" sub="Faster arrival time" color="#ef4444" />
            </div>

            {/* Charts Section */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '30px' }}>

                {/* Wait Time Comparison */}
                <ChartCard title="🚦 Avg Wait Time (Seconds) - 24Hr A3C vs Baseline Prediction">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={waitTimeData}>
                            <defs>
                                <linearGradient id="colorBase" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorAi" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                            <XAxis dataKey="time" stroke="#94a3b8" tickLine={false} axisLine={false} />
                            <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }}
                            />
                            <Area type="monotone" dataKey="baseline" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorBase)" name="Fixed Signal" />
                            <Area type="monotone" dataKey="ai" stroke="#22c55e" strokeWidth={2} fillOpacity={1} fill="url(#colorAi)" name="AI Agent" />
                        </AreaChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* Emissions Saved */}
                <ChartCard title="🌱 Fuel Savings (Gallons/Day)">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={EMISSIONS_DATA}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                            <XAxis dataKey="day" stroke="#94a3b8" tickLine={false} axisLine={false} />
                            <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }}
                                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                            />
                            <Bar dataKey="saved" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Fuel Saved" />
                        </BarChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* Intersection Comparison */}
                <ChartCard title="🏢 Intersection Performance Comparison">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={[
                            { name: 'INT_1', vehicles: 450, waitTime: 12, queue: 8 },
                            { name: 'INT_2', vehicles: 620, waitTime: 18, queue: 14 },
                            { name: 'INT_3', vehicles: 310, waitTime: 9, queue: 5 },
                            { name: 'INT_4', vehicles: 540, waitTime: 15, queue: 11 },
                        ]}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                            <XAxis dataKey="name" stroke="#94a3b8" tickLine={false} axisLine={false} />
                            <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }}
                                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                            />
                            <Bar dataKey="vehicles" fill="#3b82f6" name="Vehicle Count" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="waitTime" fill="#f59e0b" name="Avg Wait (s)" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="queue" fill="#ef4444" name="Queue Length" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </ChartCard>

            </div>
        </div>
    );
};

export default Analytics;
