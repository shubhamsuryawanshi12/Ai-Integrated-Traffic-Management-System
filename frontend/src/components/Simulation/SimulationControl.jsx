import React, { useState, useEffect } from 'react';
import { Box, Button, Typography, Paper } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import { simulationService } from '../../services/api';

function SimulationControl() {
    const [running, setRunning] = useState(false);
    const [loading, setLoading] = useState(false);

    const checkStatus = async () => {
        try {
            const res = await simulationService.getStatus();
            setRunning(res.data.running);
        } catch (err) {
            console.error("Failed to check status", err);
        }
    };

    useEffect(() => {
        checkStatus();
        const interval = setInterval(checkStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleToggle = async () => {
        setLoading(true);
        try {
            if (running) {
                await simulationService.stop();
                setRunning(false);
            } else {
                await simulationService.start();
                setRunning(true);
            }
        } catch (err) {
            console.error("Failed to toggle simulation", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Paper sx={{ p: 2, mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box>
                <Typography variant="h6">Simulation Control</Typography>
                <Typography variant="body2" color="text.secondary">
                    Status: {running ? <span style={{ color: '#00cec9', fontWeight: 'bold' }}>RUNNING</span> : <span style={{ color: 'grey' }}>STOPPED</span>}
                </Typography>
            </Box>
            <Button
                variant="contained"
                color={running ? "error" : "success"}
                startIcon={running ? <StopIcon /> : <PlayArrowIcon />}
                onClick={handleToggle}
                disabled={loading}
            >
                {running ? "Stop Simulation" : "Start Simulation"}
            </Button>
        </Paper>
    );
}

export default SimulationControl;
