import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { motion } from 'framer-motion';

const BookingConfirmPage = () => {
    const { bookingId } = useParams();
    const navigate = useNavigate();
    
    // In our backend, we don't have a single GET /bookings/{id} route documented in the spec for the driver,
    // so we'd fetch the user's bookings and filter, or just mock it here. 
    // Wait, let's fetch owner's bookings or user's bookings but since we just need the booking details, let's assume the user has the booking locally or we fetch user bookings and find it.
    
    const [booking, setBooking] = useState(null);
    const [processing, setProcessing] = useState(false);

    useEffect(() => {
        // We'll mock the booking fetch or use the user bookings. For hackathon, assuming the user ID is DRIVER_001.
        const fetchBooking = async () => {
            try {
                // Fetch all driver bookings and find the one.
                const res = await api.get(`/parking/bookings/user/DRIVER_001`);
                const b = res.data.find(b => b.id === bookingId);
                if (b) setBooking(b);
            } catch (err) {
                console.error(err);
            }
        };
        fetchBooking();
    }, [bookingId]);

    const handlePayNow = async () => {
        setProcessing(true);
        // Mock Razorpay UX delay
        setTimeout(async () => {
            try {
                const res = await api.post(`/parking/payments/${bookingId}/confirm`);
                if (res.data.success) {
                    navigate(`/parking/booking/${bookingId}/success`);
                }
            } catch (err) {
                console.error('Payment failed', err);
                alert('Payment failed. Try again.');
                setProcessing(false);
            }
        }, 1500);
    };

    if (!booking) return <div style={{ color: 'white', padding: '24px' }}>Loading...</div>;

    const start = new Date(booking.start_time);
    const end = new Date(booking.end_time);

    return (
        <div style={{ padding: '24px', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ maxWidth: '400px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <h1 style={{ fontSize: '24px', textAlign: 'center', margin: '20px 0' }}>Confirm Booking</h1>

                <div style={{ backgroundColor: '#1e293b', borderRadius: '16px', padding: '24px', border: '1px solid #334155' }}>
                    <h3 style={{ margin: '0 0 4px 0', fontSize: '18px' }}>{booking.parking_name}</h3>
                    
                    <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: '#94a3b8' }}>Start</span>
                            <strong>{start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: '#94a3b8' }}>End</span>
                            <strong>{end.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</strong>
                        </div>
                        
                        <div style={{ height: '1px', backgroundColor: '#334155', margin: '8px 0' }} />
                        
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px' }}>
                            <span style={{ color: '#94a3b8' }}>Platform Fee</span>
                            <span style={{ color: '#f8fafc' }}>₹{booking.commission_amount}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px' }}>
                            <span style={{ color: '#94a3b8' }}>Parking Fee</span>
                            <span style={{ color: '#f8fafc' }}>₹{booking.owner_amount}</span>
                        </div>
                        
                        <div style={{ height: '1px', backgroundColor: '#334155', margin: '8px 0' }} />

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '16px', fontWeight: 'bold' }}>To Pay</span>
                            <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>₹{booking.total_amount}</span>
                        </div>
                    </div>
                </div>

                <motion.button 
                    whileTap={{ scale: 0.95 }}
                    onClick={handlePayNow}
                    disabled={processing}
                    style={{ 
                        width: '100%', backgroundColor: processing ? '#475569' : '#10b981', 
                        color: 'white', padding: '16px', borderRadius: '12px', fontWeight: 'bold', fontSize: '16px', border: 'none', cursor: processing ? 'default' : 'pointer'
                    }}
                >
                    {processing ? 'Processing Secure Payment...' : `Pay ₹${booking.total_amount} Now`}
                </motion.button>
            </div>
        </div>
    );
};

export default BookingConfirmPage;
