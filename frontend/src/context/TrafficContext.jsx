import React, { createContext, useContext, useState, useEffect } from 'react';
import WebSocketService from '../services/websocket';

const TrafficContext = createContext();

// Mock data for when WebSocket is not connected
const MOCK_INTERSECTIONS = [
    {
        id: "INT_A1",
        name: "Main St & 1st Ave",
        current_status: { phase: "green" },
        traffic_data: { vehicle_count: 25, average_wait_time: 12.5 },
        location: { x: 0, y: 0 }
    },
    {
        id: "INT_A2",
        name: "Main St & 2nd Ave",
        current_status: { phase: "red" },
        traffic_data: { vehicle_count: 42, average_wait_time: 28.3 },
        location: { x: 100, y: 0 }
    },
    {
        id: "INT_B1",
        name: "Oak St & 1st Ave",
        current_status: { phase: "yellow" },
        traffic_data: { vehicle_count: 15, average_wait_time: 8.2 },
        location: { x: 0, y: 100 }
    },
    {
        id: "INT_B2",
        name: "Oak St & 2nd Ave",
        current_status: { phase: "green" },
        traffic_data: { vehicle_count: 33, average_wait_time: 15.7 },
        location: { x: 100, y: 100 }
    },
    {
        id: "INT_C1",
        name: "Park St & 1st Ave",
        current_status: { phase: "red" },
        traffic_data: { vehicle_count: 50, average_wait_time: 35.0 },
        location: { x: 200, y: 50 }
    },
    {
        id: "INT_C2",
        name: "Park St & 2nd Ave",
        current_status: { phase: "green" },
        traffic_data: { vehicle_count: 18, average_wait_time: 9.5 },
        location: { x: 200, y: 150 }
    }
];

export const TrafficProvider = ({ children }) => {
    const [intersections, setIntersections] = useState(MOCK_INTERSECTIONS);
    const [historicalData, setHistoricalData] = useState([]);
    const [currentDecision, setCurrentDecision] = useState(null);
    const [emergencyAlert, setEmergencyAlert] = useState(null);
    const [metrics, setMetrics] = useState({});
    const [isConnected, setIsConnected] = useState(false);
    const [lastUpdate, setLastUpdate] = useState(null);
    const [useMockData, setUseMockData] = useState(true);

    useEffect(() => {
        // Connect WebSocket
        WebSocketService.connect();

        // Listen for updates
        WebSocketService.on('connection_status', ({ connected }) => {
            console.log("WebSocket connection status:", connected);
            setIsConnected(connected);
        });

        WebSocketService.on('traffic_update', (data) => {
            console.log("WebSocket: traffic_update received", data);
            setUseMockData(false); // Disable mock data once we get real data

            if (data.intersections && data.intersections.length > 0) {
                setIntersections(data.intersections);
            }

            if (data.snapshot) {
                setHistoricalData(prev => [...prev, data.snapshot].slice(-500));
            }
            setLastUpdate(new Date());
        });

        WebSocketService.on('ai_decision', (decision) => {
            setCurrentDecision(decision);
        });

        WebSocketService.on('emergency_alert', (alert) => {
            setEmergencyAlert(alert);
            setTimeout(() => setEmergencyAlert(null), 30000);
        });

        WebSocketService.on('metrics', (metrics) => {
            setMetrics(metrics);
        });

        // Simulate mock data updates when not connected
        const mockInterval = setInterval(() => {
            if (useMockData) {
                // Update mock data randomly
                setIntersections(prev => prev.map(int => ({
                    ...int,
                    current_status: {
                        phase: ['green', 'yellow', 'red'][Math.floor(Math.random() * 3)]
                    },
                    traffic_data: {
                        vehicle_count: Math.floor(Math.random() * 60) + 5,
                        average_wait_time: Math.random() * 40 + 5
                    }
                })));

                // Add mock historical data
                const timestamp = Date.now();

                // Fetch REAL camera data if available
                fetch('http://localhost:5000/api/latest')
                    .then(res => res.json())
                    .then(camData => {
                        if (camData && camData.vehicles) {
                            setIntersections(prev => prev.map(int => {
                                // Update 'INT_A1' with REAL CAMERA DATA
                                if (int.id === 'INT_A1') {
                                    return {
                                        ...int,
                                        traffic_data: {
                                            vehicle_count: camData.vehicles.total || 0,
                                            average_wait_time: (camData.vehicles.queue || 0) * 2 + 5
                                        }
                                    };
                                }
                                // Keep other intersections random
                                return {
                                    ...int,
                                    current_status: {
                                        phase: ['green', 'yellow', 'red'][Math.floor(Math.random() * 3)]
                                    },
                                    traffic_data: {
                                        vehicle_count: Math.floor(Math.random() * 60) + 5,
                                        average_wait_time: Math.random() * 40 + 5
                                    }
                                };
                            }));

                            // Log real data point
                            setHistoricalData(prev => [...prev, {
                                timestamp,
                                avg_queue_length: camData.vehicles.queue || 0
                            }].slice(-100));
                        } else {
                            throw new Error("No camera data");
                        }
                    })
                    .catch(() => {
                        // Fallback to pure mock if camera offline
                        setIntersections(prev => prev.map(int => ({
                            ...int,
                            current_status: {
                                phase: ['green', 'yellow', 'red'][Math.floor(Math.random() * 3)]
                            },
                            traffic_data: {
                                vehicle_count: Math.floor(Math.random() * 60) + 5,
                                average_wait_time: Math.random() * 40 + 5
                            }
                        })));
                        setHistoricalData(prev => [...prev, {
                            timestamp,
                            avg_queue_length: Math.random() * 20 + 5
                        }].slice(-100));
                    });
            }
        }, 3000);

        return () => {
            WebSocketService.disconnect();
            clearInterval(mockInterval);
        };
    }, [useMockData]);

    const value = {
        intersections,
        historicalData,
        currentDecision,
        emergencyAlert,
        metrics,
        isConnected,
        lastUpdate,
        useMockData,
        getIntersectionById: (id) => intersections.find(i => i.id === id),
        getHistoricalRange: (startTime, endTime) =>
            historicalData.filter(d => d.timestamp >= startTime && d.timestamp <= endTime),
    };

    return (
        <TrafficContext.Provider value={value}>
            {children}
        </TrafficContext.Provider>
    );
};

export const useTraffic = () => {
    const context = useContext(TrafficContext);
    if (!context) {
        throw new Error('useTraffic must be used within TrafficProvider');
    }
    return context;
};
