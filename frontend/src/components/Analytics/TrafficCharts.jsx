import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { Paper, Typography, Grid } from '@mui/material';
import { useTraffic } from '../../context/TrafficContext';

function TrafficCharts() {
    const { historicalData, intersections } = useTraffic();

    // Transform data for bar chart - flatten nested vehicle_count
    const throughputData = intersections.map(int => ({
        name: int.name || int.id,
        vehicles: int.traffic_data?.vehicle_count || 0,
        waitTime: int.traffic_data?.average_wait_time || 0,
        phase: int.current_status?.phase || 'red'
    }));

    // Transform historical data for Area Chart (Queue Length)
    const queueData = historicalData.length > 0
        ? historicalData.map(d => ({
            timestamp: new Date(d.timestamp).toLocaleTimeString(),
            avgQueueLength: d.avg_queue_length || 0
        }))
        : // Generate mock data if empty
        Array.from({ length: 20 }, (_, i) => ({
            timestamp: new Date(Date.now() - (20 - i) * 3000).toLocaleTimeString(),
            avgQueueLength: Math.random() * 20 + 5
        }));

    const getBarColor = (vehicles) => {
        if (vehicles > 40) return '#ef4444'; // Red - congested
        if (vehicles > 25) return '#eab308'; // Yellow - moderate
        return '#22c55e'; // Green - flowing
    };

    return (
        <Grid container spacing={3}>
            {/* Throughput Bar Chart */}
            <Grid size={{ xs: 12, lg: 6 }}>
                <Paper sx={{
                    p: 2,
                    bgcolor: '#1e293b',
                    borderRadius: 2,
                    border: '1px solid #334155'
                }}>
                    <Typography variant="h6" gutterBottom sx={{ color: 'white' }}>
                        Real-Time Throughput
                    </Typography>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={throughputData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis
                                dataKey="name"
                                stroke="#94a3b8"
                                tick={{ fontSize: 10 }}
                                angle={-15}
                                textAnchor="end"
                            />
                            <YAxis stroke="#94a3b8" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#0f172a',
                                    color: '#fff',
                                    border: '1px solid #334155',
                                    borderRadius: 8
                                }}
                                formatter={(value, name) => [value, name === 'vehicles' ? 'Vehicles' : name]}
                            />
                            <Bar dataKey="vehicles" name="Vehicles" radius={[4, 4, 0, 0]}>
                                {throughputData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={getBarColor(entry.vehicles)} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </Paper>
            </Grid>

            {/* Queue Length Trends */}
            <Grid size={{ xs: 12, lg: 6 }}>
                <Paper sx={{
                    p: 2,
                    bgcolor: '#1e293b',
                    borderRadius: 2,
                    border: '1px solid #334155'
                }}>
                    <Typography variant="h6" gutterBottom sx={{ color: 'white' }}>
                        Queue Length Trends
                    </Typography>
                    <ResponsiveContainer width="100%" height={250}>
                        <AreaChart data={queueData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorQueue" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.1} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis
                                dataKey="timestamp"
                                stroke="#94a3b8"
                                tick={{ fontSize: 10 }}
                                interval="preserveStartEnd"
                            />
                            <YAxis stroke="#94a3b8" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#0f172a',
                                    color: '#fff',
                                    border: '1px solid #334155',
                                    borderRadius: 8
                                }}
                            />
                            <Area
                                type="monotone"
                                dataKey="avgQueueLength"
                                stroke="#8B5CF6"
                                strokeWidth={2}
                                fillOpacity={1}
                                fill="url(#colorQueue)"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </Paper>
            </Grid>
        </Grid>
    );
}

export default TrafficCharts;
