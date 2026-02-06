import React, { useState, useEffect } from 'react';
import { Paper, Typography, Box, Grid, LinearProgress } from '@mui/material';
import { motion } from 'framer-motion';
import { useTraffic } from '../../context/TrafficContext';

// Typewriter Effect Component
function TypewriterEffect({ text, speed = 30 }) {
    const [displayText, setDisplayText] = useState('');

    useEffect(() => {
        setDisplayText('');
        let i = 0;
        const timer = setInterval(() => {
            if (i < text?.length) {
                setDisplayText(prev => prev + text.charAt(i));
                i++;
            } else {
                clearInterval(timer);
            }
        }, speed);

        return () => clearInterval(timer);
    }, [text, speed]);

    return <span>{displayText}<span className="animate-pulse">|</span></span>;
}

function ExplainabilityPanel() {
    const { currentDecision, metrics } = useTraffic();

    // Default/Mock data if no real-time decision yet
    const decision = currentDecision || {
        action_name: "Extend Green (North-South)",
        confidence: 0.92,
        reasoning: "Northbound queue length (18) exceeds threshold. Southbound flow is continuous. Cross-traffic efficiency would drop by swapping now.",
        feature_importance: [
            { name: "North Queue", impact: 0.8 },
            { name: "South Volume", impact: 0.4 },
            { name: "East Wait Time", impact: -0.2 }
        ]
    };

    return (
        <Paper sx={{ p: 3, mt: 3, borderRadius: 2, background: 'linear-gradient(to right bottom, #ffffff, #f8fafc)' }}>
            <Grid container spacing={4}>
                {/* Section 1: Current Decision */}
                <Grid item xs={12} md={4}>
                    <Box className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-100">
                        <Typography variant="overline" color="text.secondary">Current Decision</Typography>
                        <motion.div
                            key={decision.action_name}
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                        >
                            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#2563EB', my: 1 }}>
                                {decision.action_name}
                            </Typography>
                        </motion.div>

                        <Box sx={{ mt: 3 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="body2">Confidence</Typography>
                                <Typography variant="body2" fontWeight="bold">{(decision.confidence * 100).toFixed(1)}%</Typography>
                            </Box>
                            <LinearProgress
                                variant="determinate"
                                value={decision.confidence * 100}
                                sx={{ height: 10, borderRadius: 5, bgcolor: '#E2E8F0', '& .MuiLinearProgress-bar': { bgcolor: '#3B82F6' } }}
                            />
                        </Box>
                    </Box>
                </Grid>

                {/* Section 2: Reasoning & Feature Importance */}
                <Grid item xs={12} md={8}>
                    {/* Natural Language Explanation */}
                    <Box sx={{ mb: 4, p: 2, borderLeft: '4px solid #3B82F6', bgcolor: '#EFF6FF', borderRadius: 1 }}>
                        <Box sx={{ display: 'flex', gap: 2 }}>
                            <span style={{ fontSize: '1.5rem' }}>💡</span>
                            <Box>
                                <Typography variant="subtitle1" fontWeight="bold" color="primary.main">Why This Decision?</Typography>
                                <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                                    <TypewriterEffect text={decision.reasoning} />
                                </Typography>
                            </Box>
                        </Box>
                    </Box>

                    {/* Feature Importance (SHAP) */}
                    <Typography variant="h6" gutterBottom>Decision Factors (SHAP Values)</Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        {decision.feature_importance.map((feature, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ x: -20, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                transition={{ delay: idx * 0.1 }}
                            >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                    <Typography variant="body2" sx={{ width: 100, fontWeight: 'medium' }}>{feature.name}</Typography>
                                    <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', height: 24, bgcolor: '#F1F5F9', borderRadius: 1, position: 'relative', overflow: 'hidden' }}>
                                        {/* Center Line */}
                                        <div style={{ position: 'absolute', left: '50%', height: '100%', width: '1px', backgroundColor: '#CBD5E1' }} />

                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${Math.abs(feature.impact) * 50}%` }}
                                            transition={{ duration: 1 }}
                                            style={{
                                                height: '100%',
                                                backgroundColor: feature.impact > 0 ? '#10B981' : '#EF4444',
                                                marginLeft: feature.impact > 0 ? '50%' : `calc(50% - ${Math.abs(feature.impact) * 50}%)`,
                                                borderRadius: 4
                                            }}
                                        />
                                    </Box>
                                    <Typography variant="caption" sx={{ width: 60, textAlign: 'right', fontWeight: 'bold', color: feature.impact > 0 ? 'success.main' : 'error.main' }}>
                                        {feature.impact > 0 ? '+' : ''}{(feature.impact * 100).toFixed(0)}%
                                    </Typography>
                                </Box>
                            </motion.div>
                        ))}
                    </Box>
                </Grid>
            </Grid>
        </Paper>
    );
}

export default ExplainabilityPanel;
