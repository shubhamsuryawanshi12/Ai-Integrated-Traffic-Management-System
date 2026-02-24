import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import MockDataViewer from './pages/MockDataViewer';
import { CssBaseline } from '@mui/material';
import { ThemeProvider } from './context/ThemeContext';

function App() {
    return (
        <ThemeProvider>
            <CssBaseline />
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/mock-data" element={<MockDataViewer />} />
            </Routes>
        </ThemeProvider>
    );
}

export default App;
