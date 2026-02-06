import React, { useState, useEffect } from 'react';
import TrafficMap from '../components/Dashboard/TrafficMap';
import TrafficCharts from '../components/Analytics/TrafficCharts';
import ExplainabilityPanel from '../components/Dashboard/ExplainabilityPanel';
import CameraFeed from '../components/Dashboard/CameraFeed';
import { TrafficProvider, useTraffic } from '../context/TrafficContext';

// Import Leaflet CSS (REQUIRED!)
import 'leaflet/dist/leaflet.css';

function DashboardContent() {
    const [simulationRunning, setSimulationRunning] = useState(false);
    const { intersections, isConnected } = useTraffic();

    const toggleSimulation = async () => {
        try {
            const endpoint = simulationRunning ? 'stop' : 'start';
            await fetch(`http://localhost:8000/api/v1/simulation/${endpoint}`, { method: 'POST' });
            setSimulationRunning(!simulationRunning);
        } catch (error) {
            console.error('Failed to toggle simulation:', error);
        }
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
            backgroundColor: '#0f172a',
            minHeight: '100vh',
            color: '#fff',
            padding: '20px',
        }}>
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
                    <p style={{ color: '#94a3b8', margin: '8px 0 0 0' }}>
                        AI-Powered Traffic Orchestration System
                    </p>
                </div>

                {/* Simulation Control */}
                <div style={{
                    backgroundColor: '#1e293b',
                    padding: '20px',
                    borderRadius: '12px',
                    border: '1px solid #334155',
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
                        <span style={{ color: '#94a3b8', fontSize: '14px' }}>Status: </span>
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
                <StatCard title="System Status" value={isConnected ? 'Online' : 'Offline'} color={isConnected ? '#8b5cf6' : '#ef4444'} />
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
                    backgroundColor: '#1e293b',
                    padding: '20px',
                    borderRadius: '12px',
                    border: '1px solid #334155',
                }}>
                    <h2 style={{
                        fontSize: '20px',
                        marginBottom: '15px',
                        color: '#fff',
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

            {/* Charts Grid */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
                gap: '20px',
                marginBottom: '20px',
            }}>
                <TrafficCharts />
            </div>

            {/* AI Explainability */}
            <div style={{
                backgroundColor: '#1e293b',
                padding: '20px',
                borderRadius: '12px',
                border: '1px solid #334155',
            }}>
                <h2 style={{
                    fontSize: '20px',
                    marginBottom: '15px',
                    color: '#fff',
                }}>
                    🤖 AI Decision Explainability
                </h2>
                <ExplainabilityPanel />
            </div>
        </div>
    );
}

// Stat Card Component
function StatCard({ title, value, color }) {
    return (
        <div style={{
            backgroundColor: '#1e293b',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid #334155',
        }}>
            <p style={{
                color: '#94a3b8',
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
