import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const MyBookingsPage = () => {
    const { currentUser } = useAuth();
    const navigate = useNavigate();
    const [bookings, setBookings] = useState([]);
    
    useEffect(() => {
        const fetchBookings = async () => {
            try {
                const userId = currentUser ? currentUser.id : 'DRIVER_001';
                const res = await api.get(`/parking/bookings/user/${userId}`);
                // Sort newest first
                const sorted = res.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                setBookings(sorted);
            } catch (err) {
                console.error(err);
            }
        };
        fetchBookings();
    }, [currentUser]);

    const handleCancel = async (bookingId) => {
        if (!window.confirm("Are you sure you want to cancel this booking?")) return;
        try {
            const res = await api.post(`/parking/bookings/${bookingId}/cancel`);
            if (res.data.success) {
                // Update local state
                setBookings(prev => prev.map(b => b.id === bookingId ? { ...b, status: 'cancelled' } : b));
            }
        } catch (err) {
            alert('Failed to cancel booking.');
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'confirmed': return <span style={{ color: '#10b981', backgroundColor: '#10b98122', padding: '4px 8px', borderRadius: '8px', fontSize: '12px', fontWeight: 'bold' }}>Confirmed</span>;
            case 'cancelled': return <span style={{ color: '#ef4444', backgroundColor: '#ef444422', padding: '4px 8px', borderRadius: '8px', fontSize: '12px', fontWeight: 'bold' }}>Cancelled</span>;
            case 'pending': return <span style={{ color: '#f59e0b', backgroundColor: '#f59e0b22', padding: '4px 8px', borderRadius: '8px', fontSize: '12px', fontWeight: 'bold' }}>Pending Payment</span>;
            case 'completed': return <span style={{ color: '#64748b', backgroundColor: '#64748b22', padding: '4px 8px', borderRadius: '8px', fontSize: '12px', fontWeight: 'bold' }}>Completed</span>;
            default: return null;
        }
    };

    return (
        <div style={{ backgroundColor: '#0f172a', minHeight: '100vh', padding: '24px', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ maxWidth: '600px', margin: '0 auto' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '24px', gap: '16px' }}>
                    <button onClick={() => navigate('/citizen')} style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '24px', cursor: 'pointer' }}>←</button>
                    <h1 style={{ margin: 0, fontSize: '24px' }}>My Bookings</h1>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {bookings.length === 0 ? (
                        <div style={{ color: '#94a3b8', textAlign: 'center', padding: '40px' }}>No bookings found.</div>
                    ) : (
                        bookings.map(b => {
                            const start = new Date(b.start_time);
                            const end = new Date(b.end_time);
                            const isFuture = start > new Date();

                            return (
                                <div key={b.id} style={{ backgroundColor: '#1e293b', borderRadius: '16px', padding: '20px', border: '1px solid #334155' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                                        <h3 style={{ margin: 0, fontSize: '16px' }}>{b.parking_name}</h3>
                                        {getStatusBadge(b.status)}
                                    </div>
                                    
                                    <div style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '16px' }}>
                                        {start.toLocaleDateString()} • {start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - {end.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                    </div>
                                    
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div style={{ fontSize: '18px', fontWeight: 'bold' }}>₹{b.total_amount}</div>
                                        {b.status === 'confirmed' && isFuture && (
                                            <button 
                                                onClick={() => handleCancel(b.id)}
                                                style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid #ef4444', backgroundColor: 'transparent', color: '#ef4444', cursor: 'pointer', fontSize: '13px', fontWeight: 'bold' }}
                                            >
                                                Cancel
                                            </button>
                                        )}
                                        {b.status === 'pending' && (
                                            <button 
                                                onClick={() => navigate(`/parking/booking/${b.id}/confirm`)}
                                                style={{ padding: '8px 16px', borderRadius: '8px', border: 'none', backgroundColor: '#3b82f6', color: 'white', cursor: 'pointer', fontSize: '13px', fontWeight: 'bold' }}
                                            >
                                                Pay Now
                                            </button>
                                        )}
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>
        </div>
    );
};

export default MyBookingsPage;
