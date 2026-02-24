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
    const [systemData, setSystemData] = useState({
        weather: 'clear',
        co2_saved_kg: 0,
        emergency_active: false
    });

    useEffect(() => {
        // Connect WebSocket
        WebSocketService.connect();

        // WebSocket Event Listeners
        const onConnect = () => {
            console.log("WebSocket Connected");
            setIsConnected(true);
        };

        const onDisconnect = () => {
            console.log("WebSocket Disconnected");
            setIsConnected(false);
            setUseMockData(true); // Revert to mock if disconnected
        };

        const onTrafficUpdate = (data) => {
            // console.log("WebSocket: traffic_update received", data);
            setIsConnected(true);
            setUseMockData(false); // We have real data

            if (data.intersections) {
                setIntersections(data.intersections);
            }

            if (data.snapshot) {
                setHistoricalData(prev => {
                    const newData = [...prev, data.snapshot];
                    return newData.slice(-50); // Keep last 50 points
                });

                // Extract system-wide metadata
                setSystemData({
                    weather: data.snapshot.weather || 'clear',
                    co2_saved_kg: data.snapshot.co2_saved_kg || 0,
                    emergency_active: data.snapshot.emergency_active || false
                });
            }
            setLastUpdate(new Date());
        };

        const onAiDecision = (decision) => setCurrentDecision(decision);
        const onEmergency = (alert) => {
            setEmergencyAlert(alert);
            setTimeout(() => setEmergencyAlert(null), 30000);
        };
        const onMetrics = (metrics) => setMetrics(metrics);

        // Subscribe
        WebSocketService.on('connect', onConnect);
        WebSocketService.on('disconnect', onDisconnect);
        WebSocketService.on('traffic_update', onTrafficUpdate);
        WebSocketService.on('ai_decision', onAiDecision);
        WebSocketService.on('emergency_alert', onEmergency);
        WebSocketService.on('metrics', onMetrics);

        // Fallback Mock Data Loop
        const mockInterval = setInterval(() => {
            if (useMockData) {
                // Determine if we should really randomize or just valid placeholder
                // For now, randomize to show "activity" if backend is off
                setIntersections(prev => prev.map(int => ({
                    ...int,
                    current_status: {
                        phase: ['green', 'yellow', 'red'][Math.floor(Math.random() * 3)]
                    },
                    traffic_data: {
                        ...int.traffic_data,
                        vehicle_count: Math.floor(Math.random() * 60) + 5,
                        average_wait_time: Math.random() * 40 + 5
                    }
                })));

                // Add mock history point
                setHistoricalData(prev => [...prev, {
                    timestamp: Date.now(),
                    avg_queue_length: Math.random() * 20 + 5
                }].slice(-50));
            }
        }, 3000);

        return () => {
            WebSocketService.disconnect();
            clearInterval(mockInterval);
        };
    }, []);

    const value = {
        intersections,
        historicalData,
        currentDecision,
        emergencyAlert,
        metrics,
        isConnected,
        lastUpdate,
        useMockData,
        systemData,
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
