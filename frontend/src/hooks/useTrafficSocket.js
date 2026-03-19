import { useEffect, useReducer, useRef } from 'react';
import io from 'socket.io-client';

const initialState = {
    intersections: [],
    snapshot: null,
    emergencyAlerts: [],
    connected: false,
};

function trafficReducer(state, action) {
    switch (action.type) {
        case 'UPDATE_LIVE_DATA':
            return {
                ...state,
                intersections: action.payload.intersections || state.intersections,
                snapshot: action.payload.snapshot || state.snapshot,
            };
        case 'ADD_EMERGENCY_ALERT':
            // Logic to keep recent alerts
            return {
                ...state,
                emergencyAlerts: [action.payload, ...state.emergencyAlerts].slice(0, 5),
            };
        case 'SET_CONNECTION':
            return { ...state, connected: action.payload };
        default:
            return state;
    }
}

export function useTrafficSocket(serverUrl = 'http://localhost:8000') {
    const [state, dispatch] = useReducer(trafficReducer, initialState);
    const socketRef = useRef(null);
    const batchRef = useRef({ intersections: null, snapshot: null });

    useEffect(() => {
        const socket = io(serverUrl, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
        });
        socketRef.current = socket;

        socket.on('connect', () => dispatch({ type: 'SET_CONNECTION', payload: true }));
        socket.on('disconnect', () => dispatch({ type: 'SET_CONNECTION', payload: false }));

        socket.on('traffic_update', (data) => {
            // Batch updates to reduce render frequency
            batchRef.current = {
                intersections: data.intersections,
                snapshot: data.snapshot
            };
        });

        socket.on('emergency_alert', (data) => {
            dispatch({ type: 'ADD_EMERGENCY_ALERT', payload: data });
        });

        // Interval to process batched data every 5 seconds
        const batchInterval = setInterval(() => {
            if (batchRef.current.intersections || batchRef.current.snapshot) {
                dispatch({
                    type: 'UPDATE_LIVE_DATA',
                    payload: { ...batchRef.current }
                });
                batchRef.current = { intersections: null, snapshot: null };
            }
        }, 7000);

        return () => {
            socket.disconnect();
            clearInterval(batchInterval);
        };
    }, [serverUrl]);

    return {
        ...state,
        socket: socketRef.current
    };
}
