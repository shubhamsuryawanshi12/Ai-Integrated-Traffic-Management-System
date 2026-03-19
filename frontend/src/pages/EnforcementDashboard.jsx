import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AlertPanel from '../components/Dashboard/AlertPanel';
import ParkingDashboard from '../components/Dashboard/ParkingDashboard';
import { useAuth } from '../context/AuthContext';

function EnforcementDashboard() {
    const navigate = useNavigate();
    const { role } = useAuth();

    return (
        <div style={{
            backgroundColor: '#0f172a',
            minHeight: '100vh',
            color: '#fff',
            padding: '20px',
            fontFamily: 'Inter, sans-serif'
        }}>
            {/* Header */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '30px',
                borderBottom: '1px solid #334155',
                paddingBottom: '20px'
            }}>
                <div>
                    <h1 style={{
                        fontSize: '32px', margin: '0 0 8px 0',
                        color: '#fff', display: 'flex', alignItems: 'center', gap: '12px'
                    }}>
                        🚨 Enforcement Operations Center
                    </h1>
                    <p style={{ color: '#94a3b8', margin: 0 }}>
                        Monitoring Hawkers, Obstructions, and City Parking Violations
                    </p>
                </div>

                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    <span style={{ fontSize: '13px', backgroundColor: '#334155', padding: '6px 12px', borderRadius: '16px', color: '#cbd5e1' }}>
                        Active Role: <strong>{role.toUpperCase()}</strong>
                    </span>
                    <button
                        onClick={() => navigate('/')}
                        style={{
                            backgroundColor: '#3b82f6', color: '#fff', border: 'none',
                            padding: '10px 16px', borderRadius: '8px', cursor: 'pointer',
                            fontWeight: 'bold', fontSize: '14px'
                        }}
                    >
                        Switch Role
                    </button>
                    {(role === 'admin' || role === 'traffic_police') && (
                        <button
                            onClick={() => navigate('/dashboard')}
                            style={{
                                backgroundColor: '#10b981', color: '#fff', border: 'none',
                                padding: '10px 16px', borderRadius: '8px', cursor: 'pointer',
                                fontWeight: 'bold', fontSize: '14px'
                            }}
                        >
                            Traffic Dashboard
                        </button>
                    )}
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 400px) 1fr', gap: '24px' }}>
                {/* Left Column: Alerts & Cameras (Mock) */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
                        <h2 style={{ fontSize: '18px', margin: '0 0 16px 0', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>
                            📹 Live Surveillance Feeds
                        </h2>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                            <div style={{ height: '120px', backgroundColor: '#0f172a', borderRadius: '8px', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#475569', fontSize: '12px', border: '1px solid #334155' }}>
                                Cam 1: MG Road
                            </div>
                            <div style={{ height: '120px', backgroundColor: '#0f172a', borderRadius: '8px', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#475569', fontSize: '12px', border: '1px solid #334155' }}>
                                Cam 2: Station Rd
                            </div>
                            <div style={{ height: '120px', backgroundColor: '#0f172a', borderRadius: '8px', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#475569', fontSize: '12px', border: '1px solid #334155' }}>
                                Cam 3: VIP Road
                            </div>
                            <div style={{ height: '120px', backgroundColor: '#0f172a', borderRadius: '8px', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#475569', fontSize: '12px', border: '1px solid #334155' }}>
                                Cam 4: Market Sq
                            </div>
                        </div>
                    </div>

                    <AlertPanel />
                </div>

                {/* Right Column: Parking Overview */}
                <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px', height: '100%', overflow: 'hidden' }}>
                    <h2 style={{ fontSize: '18px', margin: '0 0 16px 0', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>
                        🅿️ City Parking Status & Overstays
                    </h2>

                    <div style={{ overflowY: 'auto', maxHeight: 'calc(100vh - 200px)', paddingRight: '10px' }}>
                        <ParkingDashboard />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default EnforcementDashboard;
