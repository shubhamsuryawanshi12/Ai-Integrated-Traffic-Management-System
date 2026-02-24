import React, { createContext, useContext, useState, useMemo, useEffect } from 'react';
import { ThemeProvider as MuiThemeProvider, createTheme } from '@mui/material';

const ThemeContext = createContext();

export const useThemeContext = () => useContext(ThemeContext);

export const ThemeProvider = ({ children }) => {
    const [mode, setMode] = useState(() => {
        // Load from localStorage or default to dark
        const saved = localStorage.getItem('urbanflow-theme');
        return saved || 'dark';
    });

    // Persist theme preference
    useEffect(() => {
        localStorage.setItem('urbanflow-theme', mode);
    }, [mode]);

    const toggleTheme = () => {
        setMode(prev => {
            if (prev === 'light') return 'dark';
            if (prev === 'dark') return 'bw';
            return 'light';
        });
    };

    const theme = useMemo(() => createTheme({
        palette: {
            mode: mode === 'bw' ? 'dark' : mode,
            primary: {
                main: mode === 'bw' ? '#ffffff' : (mode === 'dark' ? '#00cec9' : '#0891b2'), // Cyan/Teal
            },
            secondary: {
                main: mode === 'bw' ? '#cccccc' : '#8b5cf6', // Purple
            },
            background: {
                default: mode === 'bw' ? '#000000' : (mode === 'dark' ? '#1e1e2e' : '#f8fafc'),
                paper: mode === 'bw' ? '#111111' : (mode === 'dark' ? '#2d2d3a' : '#ffffff'),
            },
            text: {
                primary: mode === 'bw' ? '#ffffff' : (mode === 'dark' ? '#ffffff' : '#1e293b'),
                secondary: mode === 'bw' ? '#aaaaaa' : (mode === 'dark' ? '#94a3b8' : '#64748b'),
            },
        },
        typography: {
            fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
        },
        components: {
            MuiButton: {
                styleOverrides: {
                    root: {
                        borderRadius: 8,
                        textTransform: 'none',
                        fontWeight: 600,
                    },
                },
            },
            MuiPaper: {
                styleOverrides: {
                    root: {
                        backgroundImage: 'none',
                    },
                },
            },
            MuiCard: {
                styleOverrides: {
                    root: {
                        backgroundImage: 'none',
                    },
                },
            },
        },
    }), [mode]);

    return (
        <ThemeContext.Provider value={{ mode, toggleTheme }}>
            <MuiThemeProvider theme={theme}>
                {children}
            </MuiThemeProvider>
        </ThemeContext.Provider>
    );
};
