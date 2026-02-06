/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ['./src/**/*.{js,jsx,ts,tsx}'],
    theme: {
        extend: {
            colors: {
                primary: {
                    50: '#EEF2FF',
                    500: '#3B82F6',
                    900: '#1E3A8A',
                },
                success: {
                    50: '#ECFDF5',
                    500: '#10B981',
                    900: '#064E3B',
                },
                danger: {
                    50: '#FEF2F2',
                    500: '#EF4444',
                    900: '#7F1D1D',
                },
                warning: {
                    50: '#FFFBEB',
                    500: '#F59E0B',
                    900: '#78350F',
                },
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'bounce-slow': 'bounce 2s infinite',
                'spin-slow': 'spin 3s linear infinite',
            },
            boxShadow: {
                'glow-blue': '0 0 20px rgba(59, 130, 246, 0.5)',
                'glow-green': '0 0 20px rgba(16, 185, 129, 0.5)',
                'glow-red': '0 0 20px rgba(239, 68, 68, 0.5)',
            }
        },
    },
    plugins: [],
};
