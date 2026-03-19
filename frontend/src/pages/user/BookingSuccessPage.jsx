import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

const BookingSuccessPage = () => {
    const { bookingId } = useParams();
    const navigate = useNavigate();

    return (
        <div style={{ backgroundColor: '#0f172a', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
            <motion.div initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring', damping: 15 }} >
                <div style={{ width: '120px', height: '120px', borderRadius: '50%', backgroundColor: '#10b98122', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '24px' }}>
                    <div style={{ width: '80px', height: '80px', borderRadius: '50%', backgroundColor: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '40px' }}>
                        ✓
                    </div>
                </div>
            </motion.div>

            <h1 style={{ fontSize: '28px', margin: '0 0 8px 0', textAlign: 'center' }}>Booking Confirmed!</h1>
            <p style={{ color: '#94a3b8', textAlign: 'center', marginBottom: '32px' }}>
                ID: <span style={{ fontFamily: 'monospace' }}>{bookingId.split('-')[0].toUpperCase()}</span>
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%', maxWidth: '300px' }}>
                <button 
                    onClick={() => navigate('/parking/my-bookings')}
                    style={{ background: '#3b82f6', color: 'white', border: 'none', padding: '16px', borderRadius: '12px', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer' }}
                >
                    View My Bookings
                </button>
                <button 
                    onClick={() => navigate('/citizen')}
                    style={{ background: '#1e293b', color: '#f8fafc', border: '1px solid #334155', padding: '16px', borderRadius: '12px', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer' }}
                >
                    Back to Home
                </button>
            </div>
        </div>
    );
};

export default BookingSuccessPage;
