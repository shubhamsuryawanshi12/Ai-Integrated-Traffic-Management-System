import React, { useState } from 'react';
import { Box, Typography, Button, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Home() {
    const navigate = useNavigate();
    const { role, switchRole } = useAuth();

    const handleEnter = () => {
        if (role === 'enforcement') {
            navigate('/enforcement');
        } else if (role === 'citizen') {
            navigate('/citizen');
        } else if (role === 'owner') {
            navigate('/owner/my-parkings');
        } else if (role === 'admin') {
            navigate('/admin/revenue');
        } else {
            navigate('/dashboard');
        }
    };

    return (
        <Box sx={{
            height: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 3,
            backgroundColor: '#0f172a',
            color: '#fff'
        }}>
            <Typography variant="h2" component="h1" sx={{ fontWeight: 'bold', background: 'linear-gradient(45deg, #3b82f6 30%, #8b5cf6 90%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                UrbanFlow OS
            </Typography>
            <Typography variant="h5" sx={{ color: '#94a3b8' }}>
                AI-Powered Adaptive Traffic & City Management
            </Typography>

            <Box sx={{ mt: 4, width: '300px', display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControl fullWidth sx={{
                    '& .MuiInputLabel-root': { color: '#94a3b8' },
                    '& .MuiOutlinedInput-root': {
                        color: 'white',
                        '& fieldset': { borderColor: '#334155' },
                        '&:hover fieldset': { borderColor: '#3b82f6' },
                    }
                }}>
                    <InputLabel id="role-select-label">Select Your Role</InputLabel>
                    <Select
                        labelId="role-select-label"
                        id="role-select"
                        value={role}
                        label="Select Your Role"
                        onChange={(e) => switchRole(e.target.value)}
                    >
                        <MenuItem value="traffic_police">👮 Traffic Police (Signal Control)</MenuItem>
                        <MenuItem value="enforcement">🚨 Enforcement Dept (Hawker & Parking)</MenuItem>
                        <MenuItem value="admin">🏢 City Admin (Full Overview)</MenuItem>
                        <MenuItem value="citizen">📱 Local Citizen (Mobile PWA)</MenuItem>
                        <MenuItem value="owner">🚗 Parking Owner (Zones & Revenue)</MenuItem>
                    </Select>
                </FormControl>

                <Button
                    variant="contained"
                    size="large"
                    onClick={handleEnter}
                    sx={{ backgroundColor: '#3b82f6', '&:hover': { backgroundColor: '#2563eb' } }}
                >
                    Enter System
                </Button>
            </Box>
        </Box>
    );
}

export default Home;
