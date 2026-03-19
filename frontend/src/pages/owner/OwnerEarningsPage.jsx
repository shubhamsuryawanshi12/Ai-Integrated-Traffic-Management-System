import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const OwnerEarningsPage = () => {
    const navigate = useNavigate();
    const { currentUser, switchRole } = useAuth();
    const [earnings, setEarnings] = useState(null);
    const [bookings, setBookings] = useState([]);

    useEffect(() => {
        const fetchDashboardInfo = async () => {
             try {
                 const ownerId = currentUser ? currentUser.id : 'OWNER_001';
                 const [earnRes, bookRes] = await Promise.all([
                     api.get(`/parking/owner/${ownerId}/earnings`),
                     api.get(`/parking/bookings/owner/${ownerId}`)
                 ]);
                 setEarnings(earnRes.data);
                 
                 // Process chart data: sum net earnings by parking zone
                 const zoneMap = {};
                 bookRes.data.filter(b => b.status === 'confirmed').forEach(b => {
                     zoneMap[b.parking_name] = (zoneMap[b.parking_name] || 0) + b.owner_amount;
                 });
                 
                 const chartData = Object.keys(zoneMap).map(k => ({
                     name: k,
                     NetEarnings: zoneMap[k]
                 }));
                 setBookings(chartData);

             } catch(err) {
                 console.error(err);
             }
        };
        fetchDashboardInfo();
    }, [currentUser]);

    if (!earnings) return <div style={{ color: 'white', padding: '24px' }}>Loading...</div>;

    return (
        <div style={{ padding: '24px', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
                 <div style={{ padding: '20px', borderRadius: '16px', backgroundColor: '#1e293b', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                     <div style={{ display: 'flex', gap: '16px' }}>
                        <button onClick={() => navigate('/owner/my-parkings')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>My Zones</button>
                        <button onClick={() => navigate('/owner/bookings')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Bookings</button>
                        <button onClick={() => navigate('/owner/earnings')} style={{ backgroundColor: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Earnings</button>
                     </div>
                     <div style={{ display: 'flex', gap: '16px' }}>
                        <button onClick={() => navigate('/owner/add-parking')} style={{ backgroundColor: '#10b981', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>+ Add New Zone</button>
                        <button onClick={() => { switchRole('citizen'); navigate('/'); }} style={{ backgroundColor: '#475569', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Logout</button>
                     </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px', marginBottom: '24px' }}>
                    <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155' }}>
                        <div style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '8px' }}>Total Payouts (Gross)</div>
                        <div style={{ fontSize: '32px', fontWeight: 'bold' }}>₹{earnings.total_revenue}</div>
                    </div>
                    <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155' }}>
                        <div style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '8px' }}>Commission Paid (-10%)</div>
                        <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#f87171' }}>-₹{earnings.total_commission_paid}</div>
                    </div>
                    <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #3b82f6' }}>
                        <div style={{ color: '#60a5fa', fontSize: '13px', marginBottom: '8px' }}>Your Net Earnings</div>
                        <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#3b82f6' }}>₹{earnings.owner_net_earnings}</div>
                    </div>
                    <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155' }}>
                        <div style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '8px' }}>Successful Bookings</div>
                        <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{earnings.total_bookings}</div>
                    </div>
                </div>

                <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155' }}>
                    <h3 style={{ margin: '0 0 24px 0', fontSize: '18px' }}>Earnings by Property</h3>
                    <div style={{ height: '350px', width: '100%' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={bookings} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                <XAxis dataKey="name" stroke="#94a3b8" axisLine={false} tickLine={false} />
                                <YAxis stroke="#94a3b8" axisLine={false} tickLine={false} tickFormatter={(val) => `₹${val}`} />
                                <Tooltip 
                                    cursor={{fill: '#334155', opacity: 0.4}}
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '8px' }}
                                />
                                <Bar dataKey="NetEarnings" fill="#10b981" radius={[8, 8, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default OwnerEarningsPage;
