import axios from 'axios';

// Create axios instance with base URL
// In development with Docker, localhost:8000 is accessible if ports mapped
const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const trafficService = {
    getAllIntersections: async () => {
        const response = await api.get('/traffic/');
        return response.data;
    },

    getIntersectionStatus: async (id) => {
        const response = await api.get(`/traffic/${id}`);
        return response.data;
    },

    updateSignal: async (id, state) => {
        const response = await api.post(`/traffic/${id}/control`, state);
        return response.data;
    }
};

export const simulationService = {
    start: async () => api.post('/simulation/start'),
    stop: async () => api.post('/simulation/stop'),
    getStatus: async () => api.get('/simulation/status'),
};

export default api;
