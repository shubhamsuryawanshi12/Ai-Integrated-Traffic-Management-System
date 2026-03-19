import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import TrafficMap from '../components/Dashboard/TrafficMap';
import TrafficCharts from '../components/Analytics/TrafficCharts';
import ExplainabilityPanel from '../components/Dashboard/ExplainabilityPanel';
import CameraFeed from '../components/Dashboard/CameraFeed';
import Chatbot from '../components/Dashboard/Chatbot';
import AlertPanel from '../components/Dashboard/AlertPanel';
import { TrafficProvider, useTraffic } from '../context/TrafficContext';
import { useThemeContext } from '../context/ThemeContext';

// Import Leaflet CSS (REQUIRED!)
import 'leaflet/dist/leaflet.css';

function DashboardContent() {
    const navigate = useNavigate();
    const [simulationRunning, setSimulationRunning] = useState(false);
    const { intersections, isConnected, systemData } = useTraffic();
    const { mode, toggleTheme } = useThemeContext();

    // Get theme-aware colors
    const bgColor = mode === 'bw' ? '#000000' : (mode === 'dark' ? '#0f172a' : '#f8fafc');
    const cardBgColor = mode === 'bw' ? '#111111' : (mode === 'dark' ? '#1e293b' : '#ffffff');
    const borderColor = mode === 'bw' ? '#333333' : (mode === 'dark' ? '#334155' : '#e2e8f0');
    const textPrimary = mode === 'bw' ? '#ffffff' : (mode === 'dark' ? '#ffffff' : '#1e293b');
    const textSecondary = mode === 'bw' ? '#aaaaaa' : (mode === 'dark' ? '#94a3b8' : '#64748b');
    const accentColor = mode === 'bw' ? '#ffffff' : '#3b82f6';

    const toggleSimulation = async () => {
        try {
            const endpoint = simulationRunning ? 'stop' : 'start';
            await fetch(`http://localhost:8000/api/v1/simulation/${endpoint}`, { method: 'POST' });
            setSimulationRunning(!simulationRunning);
        } catch (error) {
            console.error('Failed to toggle simulation:', error);
        }
    };

    const triggerEmergency = async () => {
        try {
            await fetch(`http://localhost:8000/api/v1/simulation/emergency?active=true&intersection_id=INT_1`, { method: 'POST' });
            setTimeout(() => {
                fetch(`http://localhost:8000/api/v1/simulation/emergency?active=false`, { method: 'POST' });
            }, 10000);
        } catch (err) { console.error(err); }
    };

    const setWeather = async (w) => {
        try {
            await fetch(`http://localhost:8000/api/v1/simulation/weather`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: w })
            });
        } catch (err) { console.error(err); }
    };

    // Check simulation status on load
    useEffect(() => {
        const checkStatus = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/v1/simulation/status');
                const data = await res.json();
                setSimulationRunning(data.running || false);
            } catch (error) {
                console.log('Backend not available');
            }
        };
        checkStatus();
    }, []);

    return (
        <div className="dashboard" style={{
            backgroundColor: bgColor,
            minHeight: '100vh',
            color: textPrimary,
            padding: '20px',
        }}>
            {/* Emergency Banner */}
            {systemData.emergency_active && (
                <div style={{
                    backgroundColor: '#ef4444',
                    color: '#fff',
                    padding: '15px',
                    borderRadius: '8px',
                    marginBottom: '20px',
                    textAlign: 'center',
                    fontWeight: 'bold',
                    fontSize: '20px',
                    boxShadow: '0 0 20px #ef4444',
                    animation: 'blink 1s infinite'
                }}>
                    🚨 EMERGENCY PREEMPTION ACTIVE: CLEARING AMBULANCE ROUTE 🚨
                </div>
            )}
            {/* Header */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '30px',
                flexWrap: 'wrap',
                gap: '20px',
            }}>
                <div>
                    <h1 style={{
                        fontSize: '48px',
                        margin: '0',
                        background: 'linear-gradient(to right, #3b82f6, #8b5cf6)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        fontWeight: 'bold',
                    }}>
                        UrbanFlow Monitor
                    </h1>
                    <p style={{ color: textSecondary, margin: '8px 0 0 0' }}>
                        AI-Powered Traffic Orchestration System
                    </p>
                </div>

                {/* Right Side Actions */}
                <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
                    {/* Theme Toggle */}
                    <button
                        onClick={toggleTheme}
                        style={{
                            backgroundColor: mode === 'dark' ? '#fbbf24' : '#1e293b',
                            color: mode === 'dark' ? '#1e293b' : '#fbbf24',
                            border: `1px solid ${mode === 'dark' ? '#fbbf24' : '#475569'}`,
                            padding: '12px 16px',
                            borderRadius: '12px',
                            cursor: 'pointer',
                            fontWeight: 'bold',
                            fontSize: '18px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            minWidth: '50px',
                            justifyContent: 'center',
                            transition: 'all 0.3s ease',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                        }}
                        title={mode === 'dark' ? 'Switch to Light Mode' : (mode === 'bw' ? 'Switch to Dark Mode' : 'Switch to BW Mode')}
                    >
                        {mode === 'dark' ? '☀️' : (mode === 'bw' ? '⚫' : '🌙')}
                    </button>
                    {/* Analytics Button */}
                    <button
                        onClick={() => navigate('/analytics')}
                        style={{
                            backgroundColor: '#3b82f6',
                            color: '#fff',
                            border: '1px solid #60a5fa',
                            padding: '20px',
                            borderRadius: '12px',
                            cursor: 'pointer',
                            fontWeight: 'bold',
                            fontSize: '14px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            height: '100%'
                        }}
                    >
                        <span>📊 View Analytics</span>
                    </button>

                    {/* Demo Controls */}
                    <div style={{
                        backgroundColor: cardBgColor,
                        padding: '15px',
                        borderRadius: '12px',
                        border: `1px solid ${borderColor}`,
                        display: 'flex',
                        gap: '10px'
                    }}>
                        <button
                            onClick={triggerEmergency}
                            style={{
                                backgroundColor: '#dc2626',
                                color: '#fff',
                                border: 'none',
                                padding: '8px 12px',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontWeight: 'bold'
                            }}
                        >
                            🚑 Trigger Siren
                        </button>
                        <select
                            onChange={(e) => setWeather(e.target.value)}
                            value={systemData.weather}
                            style={{
                                backgroundColor: '#334155',
                                color: '#fff',
                                border: 'none',
                                padding: '8px',
                                borderRadius: '6px'
                            }}
                        >
                            <option value="clear">☀️ Clear</option>
                            <option value="rain">🌧️ Rain</option>
                            <option value="fog">🌫️ Fog</option>
                        </select>
                    </div>

                    {/* Simulation Control */}
                    <div style={{
                        backgroundColor: cardBgColor,
                        padding: '20px',
                        borderRadius: '12px',
                        border: `1px solid ${borderColor}`,
                        minWidth: '200px',
                    }}>
                        <div style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{
                                width: '8px',
                                height: '8px',
                                borderRadius: '50%',
                                backgroundColor: isConnected ? '#22c55e' : '#ef4444',
                                boxShadow: isConnected ? '0 0 8px #22c55e' : '0 0 8px #ef4444',
                            }}></div>
                            <span style={{ color: textSecondary, fontSize: '14px' }}>Status: </span>
                            <span style={{
                                color: simulationRunning ? '#22c55e' : '#ef4444',
                                fontWeight: 'bold',
                                fontSize: '14px',
                            }}>
                                {simulationRunning ? 'RUNNING' : 'STOPPED'}
                            </span>
                        </div>
                        <button
                            onClick={toggleSimulation}
                            style={{
                                backgroundColor: simulationRunning ? '#ef4444' : '#22c55e',
                                color: '#fff',
                                border: 'none',
                                padding: '10px 20px',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontWeight: 'bold',
                                fontSize: '14px',
                                width: '100%',
                                transition: 'all 0.2s',
                            }}
                        >
                            {simulationRunning ? '⏸ STOP SIMULATION' : '▶ START SIMULATION'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Stats Cards */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '15px',
                marginBottom: '20px',
            }}>
                <StatCard title="Total Intersections" value={intersections.length || 9} color="#3b82f6" />
                <StatCard title="Active Vehicles" value={intersections.reduce((sum, i) => sum + (i.throughput || i.vehicles || 0), 0) || 247} color="#22c55e" />
                <StatCard title="Avg Wait Time" value={`${(intersections.reduce((sum, i) => sum + (i.queueLength || i.waitTime || 0), 0) / Math.max(intersections.length, 1)).toFixed(1)}s`} color="#f59e0b" />
                <StatCard title="Green Impact (CO2 Saved)" value={`${systemData.co2_saved_kg} kg`} color="#10b981" />
                <StatCard title="System Status" value={isConnected ? 'Online' : 'Offline'} color={isConnected ? accentColor : '#ef4444'} />
            </div>

            {/* Main Content Grid - Map & Camera */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(600px, 1fr))',
                gap: '20px',
                marginBottom: '20px',
            }}>
                {/* Traffic Map Card */}
                <div style={{
                    backgroundColor: cardBgColor,
                    padding: '20px',
                    borderRadius: '12px',
                    border: `1px solid ${borderColor}`,
                }}>
                    <h2 style={{
                        fontSize: '20px',
                        marginBottom: '15px',
                        color: textPrimary,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                    }}>
                        🗺️ Live Traffic Map
                        <span style={{
                            fontSize: '12px',
                            color: '#22c55e',
                            backgroundColor: 'rgba(34, 197, 94, 0.1)',
                            padding: '4px 8px',
                            borderRadius: '4px',
                        }}>
                            Live View
                        </span>
                    </h2>
                    <div style={{ height: '500px', width: '100%', borderRadius: '8px', overflow: 'hidden' }}>
                        <TrafficMap />
                    </div>
                </div>

                {/* Camera Feed Card */}
                <CameraFeed />
            </div>

            {/* Charts Grid & Alerts */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
                gap: '20px',
                marginBottom: '20px',
            }}>
                <TrafficCharts />
                <AlertPanel />
            </div>

            {/* AI Explainability */}
            <div style={{
                backgroundColor: cardBgColor,
                padding: '20px',
                borderRadius: '12px',
                border: `1px solid ${borderColor}`,
            }}>
                <h2 style={{
                    fontSize: '20px',
                    marginBottom: '15px',
                    color: textPrimary,
                }}>
                    🤖 AI Decision Explainability
                </h2>
                <ExplainabilityPanel />
            </div>

            {/* AI Chatbot */}
            <Chatbot />

            <style>{`
                @keyframes blink {
                    0% { opacity: 1; }
                    50% { opacity: 0.5; }
                    100% { opacity: 1; }
                }
            `}</style>
        </div>
    );
}

// Stat Card Component
function StatCard({ title, value, color }) {
    const { mode } = useThemeContext();
    const cardBgColor = mode === 'bw' ? '#111111' : (mode === 'dark' ? '#1e293b' : '#ffffff');
    const borderColor = mode === 'bw' ? '#333333' : (mode === 'dark' ? '#334155' : '#e2e8f0');
    const textSecondary = mode === 'bw' ? '#aaaaaa' : (mode === 'dark' ? '#94a3b8' : '#64748b');

    return (
        <div style={{
            backgroundColor: cardBgColor,
            padding: '20px',
            borderRadius: '12px',
            border: `1px solid ${borderColor}`,
        }}>
            <p style={{
                color: textSecondary,
                fontSize: '14px',
                margin: '0 0 8px 0',
            }}>
                {title}
            </p>
            <p style={{
                color: color,
                fontSize: '28px',
                fontWeight: 'bold',
                margin: '0',
            }}>
                {value}
            </p>
        </div>
    );
}

export default function Dashboard() {
    return (
        <TrafficProvider>
            <DashboardContent />
        </TrafficProvider>
    );
}
