import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const AdminApprovalsPage = () => {
    const navigate = useNavigate();
    const [pending, setPending] = useState([]);

    const fetchPending = async () => {
        try {
            const res = await api.get('/parking/admin/pending');
            setPending(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        fetchPending();
    }, []);

    const handleAction = async (zoneId, action) => {
        try {
            await api.post(`/parking/admin/${action}/${zoneId}`);
            fetchPending(); // Refresh list
        } catch (err) {
            alert(`Failed to ${action} zone.`);
        }
    };

    return (
        <div style={{ padding: '24px', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
                <div style={{ padding: '20px', borderRadius: '16px', backgroundColor: '#1e293b', border: '1px solid #334155', display: 'flex', gap: '16px', marginBottom: '24px' }}>
                     <button onClick={() => navigate('/admin/revenue')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Revenue Dashboard</button>
                     <button onClick={() => navigate('/admin/parking/approvals')} style={{ backgroundColor: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Pending Approvals {pending.length > 0 && `(${pending.length})`}</button>
                     <button onClick={() => navigate('/admin/commission')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Commission Setup</button>
                     <button onClick={() => navigate('/admin/users')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>All Users</button>
                </div>

                <h1 style={{ fontSize: '24px', marginBottom: '24px' }}>Pending Zone Approvals</h1>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '20px' }}>
                    {pending.length === 0 ? <p style={{ color: '#94a3b8' }}>No pending zones.</p> : null}
                    
                    {pending.map(z => (
                        <div key={z.id} style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                                <h3 style={{ margin: 0, fontSize: '18px' }}>{z.name}</h3>
                            </div>
                            
                            <p style={{ color: '#94a3b8', fontSize: '14px', margin: '0 0 16px 0' }}>{z.address}</p>
                            
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', backgroundColor: '#0f172a', padding: '16px', borderRadius: '12px', marginBottom: '16px' }}>
                                <div><div style={{ fontSize: '12px', color: '#64748b' }}>Total Slots</div><div style={{ fontWeight: 'bold' }}>{z.total_slots}</div></div>
                                <div><div style={{ fontSize: '12px', color: '#64748b' }}>Price</div><div style={{ fontWeight: 'bold' }}>₹{z.price_per_hour}/hr</div></div>
                                <div><div style={{ fontSize: '12px', color: '#64748b' }}>Owner ID</div><div style={{ fontWeight: 'bold' }}>{z.owner_id}</div></div>
                                <div><div style={{ fontSize: '12px', color: '#64748b' }}>Type</div><div style={{ fontWeight: 'bold', textTransform: 'capitalize' }}>{z.type}</div></div>
                            </div>

                            <div style={{ display: 'flex', gap: '16px' }}>
                                <button onClick={() => handleAction(z.id, 'approve')} style={{ flex: 1, backgroundColor: '#10b981', color: 'white', padding: '12px', borderRadius: '8px', border: 'none', fontWeight: 'bold', cursor: 'pointer' }}>Approve</button>
                                <button onClick={() => handleAction(z.id, 'reject')} style={{ flex: 1, backgroundColor: 'transparent', color: '#ef4444', border: '1px solid #ef4444', padding: '12px', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>Reject</button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default AdminApprovalsPage;
