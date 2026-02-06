import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

function Home() {
    const navigate = useNavigate();

    return (
        <Box sx={{
            height: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 3
        }}>
            <Typography variant="h2" component="h1" sx={{ fontWeight: 'bold', background: 'linear-gradient(45deg, #00cec9 30%, #6c5ce7 90%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                UrbanFlow
            </Typography>
            <Typography variant="h5" color="text.secondary">
                AI-Powered Adaptive Traffic Management
            </Typography>
            <Button variant="contained" size="large" onClick={() => navigate('/dashboard')}>
                Enter Dashboard
            </Button>
        </Box>
    );
}

export default Home;
