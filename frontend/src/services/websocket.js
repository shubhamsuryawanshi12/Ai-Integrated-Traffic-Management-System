import io from 'socket.io-client';

class WebSocketService {
    constructor() {
        this.socket = null;
        this.listeners = new Map();
    }

    connect() {
        this.socket = io('http://localhost:8000', {
            transports: ['websocket', 'polling'], // Allow polling fallback
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 10,
        });

        this.socket.on('connect_error', (err) => {
            console.error("WebSocket Connection Error:", err);
        });

        this.socket.on('connect', () => {
            console.log('✅ WebSocket connected');
            this.emit('connection_status', { connected: true });
        });

        this.socket.on('disconnect', () => {
            console.log('❌ WebSocket disconnected');
            this.emit('connection_status', { connected: false });
        });

        // Real-time traffic updates (every 2 seconds)
        this.socket.on('traffic_update', (data) => {
            this.emit('traffic_update', data);
        });

        // AI decision updates
        this.socket.on('ai_decision', (decision) => {
            this.emit('ai_decision', decision);
        });

        // Prediction updates
        this.socket.on('prediction_update', (prediction) => {
            this.emit('prediction_update', prediction);
        });

        // Emergency vehicle alerts
        this.socket.on('emergency_alert', (alert) => {
            this.emit('emergency_alert', alert);
        });

        // System metrics
        this.socket.on('metrics', (metrics) => {
            this.emit('metrics', metrics);
        });

        // Parking updates
        this.socket.on('parking_update', (data) => {
            this.emit('parking_update', data);
        });
    }

    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            this.listeners.set(event, callbacks.filter(cb => cb !== callback));
        }
    }

    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(cb => cb(data));
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

const webSocketService = new WebSocketService();
export default webSocketService;
