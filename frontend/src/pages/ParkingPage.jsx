import React from 'react';
import ParkingDashboard from '../components/Dashboard/ParkingDashboard';

const ParkingPage = () => {
    return (
        <div style={{
            backgroundColor: '#0f172a',
            minHeight: '100vh',
            color: '#fff',
            padding: '32px',
            fontFamily: 'Inter, sans-serif'
        }}>
            {/* Header */}
            <div style={{ marginBottom: '32px' }}>
                <h1 style={{
                    fontSize: '28px',
                    fontWeight: 'bold',
                    margin: 0,
                    color: '#fff',
                    marginBottom: '8px'
                }}>
                    Smart Parking Central 🚗
                </h1>
                <p style={{ color: '#94a3b8', margin: 0, fontSize: '14px' }}>
                    Real-time parking zone monitoring and AI occupancy prediction.
                </p>
            </div>

            {/* Main Content */}
            <ParkingDashboard />
        </div>
    );
};

export default ParkingPage;
