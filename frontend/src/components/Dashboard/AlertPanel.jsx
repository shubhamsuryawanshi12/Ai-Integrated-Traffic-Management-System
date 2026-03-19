import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { io } from 'socket.io-client';

const AlertPanel = () => {
    const [alerts, setAlerts] = useState([]);

    useEffect(() => {
        // Connect directly to the camera server for CV alerts
        const cameraSocket = io('http://localhost:5000', {
            transports: ['websocket', 'polling']
        });

        cameraSocket.on('connect', () => {
            console.log('AlertPanel connected to Camera Server');
        });

        cameraSocket.on('hawker_alert', (alertData) => {
            const newAlert = {
                id: Date.now().toString(),
                timestamp: new Date().toLocaleTimeString(),
                message: alertData.alert_message,
                severity: alertData.severity, // 'HIGH', 'MEDIUM', 'LOW'
                type: 'hawker',
            };

            setAlerts((prev) => {
                const updated = [newAlert, ...prev].slice(0, 20); // Keep last 20
                return updated;
            });

            // Auto dismiss after 30s
            setTimeout(() => {
                setAlerts((prev) => prev.filter(a => a.id !== newAlert.id));
            }, 30000);
        });

        // Add anomaly listener here as well for Task 6 later
        // ...

        return () => {
            cameraSocket.disconnect();
        };
    }, []);

    const dismissAlert = (id) => {
        setAlerts(prev => prev.filter(a => a.id !== id));
    };

    const getSeverityStyles = (severity) => {
        switch (severity) {
            case 'HIGH':
                return { bg: '#ef4444', text: '#fee2e2', border: '#b91c1c', icon: '🚨' };
            case 'MEDIUM':
                return { bg: '#f59e0b', text: '#fef3c7', border: '#b45309', icon: '⚠️' };
            case 'LOW':
                return { bg: '#3b82f6', text: '#dbeafe', border: '#1d4ed8', icon: 'ℹ️' };
            default:
                return { bg: '#64748b', text: '#f1f5f9', border: '#475569', icon: '🔔' };
        }
    };

    return (
        <div style={{ backgroundColor: '#1e293b', borderRadius: '12px', border: '1px solid #334155', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: '400px', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0, fontSize: '16px', color: '#fff' }}>🛑 Live Security Alerts</h3>
                <span style={{ fontSize: '12px', color: '#94a3b8', background: '#334155', padding: '2px 8px', borderRadius: '12px' }}>
                    {alerts.length} Active
                </span>
            </div>

            {alerts.length === 0 ? (
                <div style={{ padding: '24px', textAlign: 'center', color: '#64748b', fontSize: '14px' }}>
                    No active alerts. Monitoring zones...
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <AnimatePresence>
                        {alerts.map(alert => {
                            const styles = getSeverityStyles(alert.severity);
                            const isHigh = alert.severity === 'HIGH';

                            return (
                                <motion.div
                                    key={alert.id}
                                    initial={{ opacity: 0, x: -20, scale: 0.95 }}
                                    animate={{ opacity: 1, x: 0, scale: 1 }}
                                    exit={{ opacity: 0, x: 20, scale: 0.95 }}
                                    transition={{ duration: 0.2 }}
                                    style={{
                                        position: 'relative',
                                        backgroundColor: styles.bg + '20', // Add transparency
                                        border: `1px solid ${styles.border}`,
                                        padding: '12px 16px',
                                        borderRadius: '8px',
                                        display: 'flex',
                                        alignItems: 'flex-start',
                                        gap: '12px',
                                        overflow: 'hidden'
                                    }}
                                >
                                    {isHigh && (
                                        <motion.div
                                            animate={{ opacity: [0.1, 0.3, 0.1] }}
                                            transition={{ repeat: Infinity, duration: 1.5 }}
                                            style={{
                                                position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                                                backgroundColor: styles.bg, zIndex: 0, pointerEvents: 'none'
                                            }}
                                        />
                                    )}

                                    <div style={{ fontSize: '20px', zIndex: 1 }}>{styles.icon}</div>
                                    <div style={{ flex: 1, zIndex: 1 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                            <span style={{ fontSize: '12px', fontWeight: 'bold', color: styles.bg }}>
                                                {alert.severity} SEVERITY
                                            </span>
                                            <span style={{ fontSize: '11px', color: '#94a3b8' }}>{alert.timestamp}</span>
                                        </div>
                                        <div style={{ fontSize: '14px', color: '#f8fafc', fontWeight: '500' }}>
                                            {alert.message}
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => dismissAlert(alert.id)}
                                        style={{
                                            background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer',
                                            fontSize: '16px', zIndex: 1, padding: '0 4px'
                                        }}
                                        title="Dismiss"
                                    >
                                        ×
                                    </button>
                                </motion.div>
                            );
                        })}
                    </AnimatePresence>
                </div>
            )}
        </div>
    );
};

export default AlertPanel;
