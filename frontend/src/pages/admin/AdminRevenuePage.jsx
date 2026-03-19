import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from 'recharts';

const AdminRevenuePage = () => {
    const navigate = useNavigate();
    const { switchRole } = useAuth();
    const [stats, setStats] = useState(null);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const res = await api.get('/parking/admin/revenue');
                setStats(res.data);
            } catch (err) {
                console.error(err);
            }
        };
        fetchStats();
    }, []);

    if (!stats) return <div style={{ color: 'white', padding: '24px' }}>Loading...</div>;

    const data = [
        { name: 'City Commission (Your cut)', value: stats.total_commission_earned, color: '#10b981' }, // Green
        { name: 'Owner Payouts', value: stats.total_owner_payouts, color: '#6366f1' }   // Indigo
    ];

    return (
        <div style={{ padding: '24px', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <h1 style={{ fontSize: '28px', margin: 0 }}>Smart City Platform</h1>
                    <button onClick={() => { switchRole('citizen'); navigate('/'); }} style={{ backgroundColor: '#475569', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Logout</button>
                </div>

                 <div style={{ padding: '20px', borderRadius: '16px', backgroundColor: '#1e293b', border: '1px solid #334155', display: 'flex', gap: '16px', marginBottom: '24px' }}>
                     <button onClick={() => navigate('/admin/revenue')} style={{ backgroundColor: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Revenue Dashboard</button>
                     <button onClick={() => navigate('/admin/parking/approvals')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Pending Approvals</button>
                     <button onClick={() => navigate('/admin/commission')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Commission Setup</button>
                     <button onClick={() => navigate('/admin/users')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>All Users</button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '24px' }}>
                    <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #10b981' }}>
                        <div style={{ color: '#34d399', fontSize: '13px', marginBottom: '8px' }}>Platform Net Revenue</div>
                        <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#10b981' }}>₹{stats.total_commission_earned}</div>
                    </div>
                    <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155' }}>
                        <div style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '8px' }}>Total System GV</div>
                        <div style={{ fontSize: '32px', fontWeight: 'bold' }}>₹{stats.total_revenue}</div>
                    </div>
                    <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155' }}>
                        <div style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '8px' }}>Active City Zones</div>
                        <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{stats.active_zones} <span style={{ fontSize: '14px', color: '#64748b' }}>({stats.pending_zones} pending)</span></div>
                    </div>
                    <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155' }}>
                        <div style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '8px' }}>Total Bookings Served</div>
                        <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{stats.total_bookings}</div>
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                    <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155', minHeight: '350px' }}>
                        <h3 style={{ margin: '0 0 24px 0', fontSize: '18px' }}>Gross Revenue Split</h3>
                        <div style={{ width: '100%', height: '280px' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie data={data} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={5} dataKey="value" stroke="none">
                                        {data.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                                    </Pie>
                                    <RechartsTooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #475569', borderRadius: '8px', color: 'white' }} itemStyle={{ color: 'white' }} formatter={(val) => `₹${val}`} />
                                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                    
                    <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
                         <div style={{ fontSize: '64px', marginBottom: '16px' }}>🏬</div>
                         <h3 style={{ margin: '0 0 8px 0', fontSize: '20px' }}>City Scalability</h3>
                         <p style={{ color: '#94a3b8', maxWidth: '300px', lineHeight: '1.6' }}>
                             By distributing the parking network to private property owners, Solapur City reduces traffic congestion and maximizes urban density limits without building entirely new civic parking structures.
                         </p>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default AdminRevenuePage;
