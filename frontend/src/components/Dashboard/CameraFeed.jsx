import React, { useState } from 'react';

const CameraFeed = () => {
    const [isLive, setIsLive] = useState(false);
    const cameraUrl = "http://localhost:5000"; // Mobile Camera Server URL

    return (
        <div style={{
            backgroundColor: '#1e293b',
            padding: '24px',
            borderRadius: '12px',
            border: '1px solid #334155',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            height: '500px',
            display: 'flex',
            flexDirection: 'column'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '20px', fontWeight: 'bold', color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>📹</span> Live Traffic Camera
                    {isLive && (
                        <span style={{ position: 'relative', display: 'flex', height: '12px', width: '12px', marginLeft: '8px' }}>
                            <span style={{
                                animation: 'ping 1s cubic-bezier(0, 0, 0.2, 1) infinite',
                                position: 'absolute',
                                display: 'inline-flex',
                                height: '100%',
                                width: '100%',
                                borderRadius: '50%',
                                backgroundColor: '#f87171',
                                opacity: 0.75
                            }}></span>
                            <span style={{
                                position: 'relative',
                                display: 'inline-flex',
                                borderRadius: '50%',
                                height: '12px',
                                width: '12px',
                                backgroundColor: '#ef4444'
                            }}></span>
                        </span>
                    )}
                </h3>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        onClick={() => setIsLive(!isLive)}
                        style={{
                            padding: '4px 12px',
                            borderRadius: '4px',
                            fontSize: '14px',
                            fontWeight: '500',
                            transition: 'colors 0.2s',
                            backgroundColor: isLive ? 'rgba(239, 68, 68, 0.2)' : '#334155',
                            color: isLive ? '#f87171' : '#94a3b8',
                            border: 'none',
                            cursor: 'pointer'
                        }}
                    >
                        {isLive ? 'LIVE' : 'OFFLINE'}
                    </button>
                    <a
                        href={`${cameraUrl}/dashboard`}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                            padding: '4px 12px',
                            backgroundColor: 'rgba(59, 130, 246, 0.2)',
                            color: '#60a5fa',
                            borderRadius: '4px',
                            fontSize: '14px',
                            textDecoration: 'none',
                            transition: 'background-color 0.2s'
                        }}
                    >
                        Open Dashboard ↗
                    </a>
                </div>
            </div>

            <div style={{
                flex: 1,
                backgroundColor: 'black',
                borderRadius: '8px',
                overflow: 'hidden',
                position: 'relative',
                border: '1px solid #334155'
            }}>
                {isLive ? (
                    <iframe
                        src={cameraUrl}
                        title="Live Camera Feed"
                        style={{ width: '100%', height: '100%', border: 'none' }}
                        allow="camera; microphone"
                        onError={() => setIsLive(false)}
                    />
                ) : (
                    <div style={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#64748b'
                    }}>
                        <svg xmlns="http://www.w3.org/2000/svg" style={{ height: '64px', width: '64px', marginBottom: '16px', opacity: 0.5 }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        <p>Camera feed offline</p>
                        <p style={{ fontSize: '12px', marginTop: '8px', color: '#475569' }}>Ensure Mobile Camera Server is running on port 5000</p>
                    </div>
                )}
            </div>

            <div style={{
                marginTop: '16px',
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '16px',
                textAlign: 'center',
                fontSize: '14px',
                color: '#94a3b8'
            }}>
                <div style={{ backgroundColor: 'rgba(15, 23, 42, 0.5)', padding: '8px', borderRadius: '4px' }}>
                    <div style={{ color: '#64748b', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>Status</div>
                    <div style={{ color: isLive ? '#4ade80' : '#ef4444', fontWeight: 'bold' }}>{isLive ? 'Connected' : 'Disconnected'}</div>
                </div>
                <div style={{ backgroundColor: 'rgba(15, 23, 42, 0.5)', padding: '8px', borderRadius: '4px' }}>
                    <div style={{ color: '#64748b', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>Source</div>
                    <div style={{ color: 'white' }}>Mobile Cam</div>
                </div>
                <div style={{ backgroundColor: 'rgba(15, 23, 42, 0.5)', padding: '8px', borderRadius: '4px' }}>
                    <div style={{ color: '#64748b', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>Detection</div>
                    <div style={{ color: '#60a5fa', fontWeight: 'bold' }}>Active</div>
                </div>
            </div>
            <style>{`
                @keyframes ping {
                    75%, 100% {
                        transform: scale(2);
                        opacity: 0;
                    }
                }
            `}</style>
        </div>
    );
};

export default CameraFeed;
