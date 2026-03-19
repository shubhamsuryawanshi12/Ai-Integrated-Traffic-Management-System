import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';

const OwnerBookingsPage = () => {
    const navigate = useNavigate();
    const { currentUser, switchRole } = useAuth();
    const [bookings, setBookings] = useState([]);
    const [filter, setFilter] = useState('all');

    useEffect(() => {
        const fetchBookings = async () => {
             try {
                 const ownerId = currentUser ? currentUser.id : 'OWNER_001';
                 const res = await api.get(`/parking/bookings/owner/${ownerId}`);
                 // Sort descending
                 const sorted = res.data.sort((a,b) => new Date(b.created_at) - new Date(a.created_at));
                 setBookings(sorted);
             } catch(err) {
                 console.error(err);
             }
        };
        fetchBookings();
    }, [currentUser]);

    const filtered = bookings.filter(b => {
        if (filter === 'all') return true;
        return b.status === filter;
    });

    return (
        <div style={{ padding: '24px', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
                 <div style={{ padding: '20px', borderRadius: '16px', backgroundColor: '#1e293b', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                     <div style={{ display: 'flex', gap: '16px' }}>
                        <button onClick={() => navigate('/owner/my-parkings')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>My Zones</button>
                        <button onClick={() => navigate('/owner/bookings')} style={{ backgroundColor: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Bookings</button>
                        <button onClick={() => navigate('/owner/earnings')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Earnings</button>
                     </div>
                     <div style={{ display: 'flex', gap: '16px' }}>
                        <button onClick={() => navigate('/owner/add-parking')} style={{ backgroundColor: '#10b981', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>+ Add New Zone</button>
                        <button onClick={() => { switchRole('citizen'); navigate('/'); }} style={{ backgroundColor: '#475569', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Logout</button>
                     </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <h1 style={{ fontSize: '24px', margin: 0 }}>All Bookings</h1>
                    <select value={filter} onChange={e => setFilter(e.target.value)} style={{ padding: '8px 16px', borderRadius: '8px', backgroundColor: '#1e293b', color: 'white', border: '1px solid #475569' }}>
                        <option value="all">All Bookings</option>
                        <option value="confirmed">Confirmed</option>
                        <option value="cancelled">Cancelled</option>
                        <option value="pending">Pending Payment</option>
                    </select>
                </div>

                <div style={{ overflowX: 'auto', backgroundColor: '#1e293b', borderRadius: '16px', border: '1px solid #334155' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8', fontSize: '13px' }}>
                                <th style={{ padding: '16px' }}>Zone</th>
                                <th style={{ padding: '16px' }}>Period</th>
                                <th style={{ padding: '16px' }}>Total Paid</th>
                                <th style={{ padding: '16px' }}>Your Cut</th>
                                <th style={{ padding: '16px' }}>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.length === 0 && (
                                <tr>
                                    <td colSpan="5" style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>No bookings found</td>
                                </tr>
                            )}
                            {filtered.map(b => (
                                <tr key={b.id} style={{ borderBottom: '1px solid #334155' }}>
                                    <td style={{ padding: '16px', fontWeight: '600' }}>{b.parking_name}</td>
                                    <td style={{ padding: '16px', fontSize: '13px', color: '#94a3b8' }}>
                                        {new Date(b.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - {new Date(b.end_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}<br/>
                                        {new Date(b.start_time).toLocaleDateString()}
                                    </td>
                                    <td style={{ padding: '16px' }}>₹{b.total_amount}</td>
                                    <td style={{ padding: '16px', color: '#10b981', fontWeight: 'bold' }}>₹{b.owner_amount}</td>
                                    <td style={{ padding: '16px' }}>
                                        <span style={{ 
                                            padding: '4px 8px', borderRadius: '8px', fontSize: '12px', fontWeight: 'bold',
                                            backgroundColor: b.status === 'confirmed' ? '#10b98122' : b.status === 'cancelled' ? '#ef444422' : '#f59e0b22',
                                            color: b.status === 'confirmed' ? '#10b981' : b.status === 'cancelled' ? '#ef4444' : '#f59e0b'
                                        }}>
                                            {b.status.toUpperCase()}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

            </div>
        </div>
    );
};

export default OwnerBookingsPage;
