import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const AdminUsersPage = () => {
    const navigate = useNavigate();
    const [users, setUsers] = useState([]);

    useEffect(() => {
        const fetchUsers = async () => {
            try {
                const res = await api.get('/parking/admin/users');
                setUsers(res.data);
            } catch (err) {
                console.error(err);
            }
        };
        fetchUsers();
    }, []);

    return (
        <div style={{ padding: '24px', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
                 <div style={{ padding: '20px', borderRadius: '16px', backgroundColor: '#1e293b', border: '1px solid #334155', display: 'flex', gap: '16px', marginBottom: '24px' }}>
                     <button onClick={() => navigate('/admin/revenue')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Revenue Dashboard</button>
                     <button onClick={() => navigate('/admin/parking/approvals')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Pending Approvals</button>
                     <button onClick={() => navigate('/admin/commission')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Commission Setup</button>
                     <button onClick={() => navigate('/admin/users')} style={{ backgroundColor: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>All Users</button>
                </div>

                <h1 style={{ fontSize: '24px', marginBottom: '24px' }}>System Users</h1>

                <div style={{ overflowX: 'auto', backgroundColor: '#1e293b', borderRadius: '16px', border: '1px solid #334155' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8', fontSize: '13px' }}>
                                <th style={{ padding: '16px' }}>User ID</th>
                                <th style={{ padding: '16px' }}>Name</th>
                                <th style={{ padding: '16px' }}>Email</th>
                                <th style={{ padding: '16px' }}>Role</th>
                                <th style={{ padding: '16px' }}>Joined Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(u => (
                                <tr key={u.id} style={{ borderBottom: '1px solid #334155' }}>
                                    <td style={{ padding: '16px', fontFamily: 'monospace', color: '#60a5fa' }}>{u.id}</td>
                                    <td style={{ padding: '16px', fontWeight: 'bold' }}>{u.name}</td>
                                    <td style={{ padding: '16px', color: '#94a3b8' }}>{u.email}</td>
                                    <td style={{ padding: '16px' }}>
                                        <span style={{ 
                                            padding: '4px 12px', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold', textTransform: 'capitalize',
                                            backgroundColor: u.role === 'admin' ? '#ef444433' : u.role === 'owner' ? '#f59e0b33' : '#3b82f633',
                                            color: u.role === 'admin' ? '#f87171' : u.role === 'owner' ? '#fbbf24' : '#60a5fa'
                                        }}>
                                            {u.role}
                                        </span>
                                    </td>
                                    <td style={{ padding: '16px', color: '#94a3b8', fontSize: '13px' }}>{new Date(u.created_at || new Date()).toLocaleDateString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

            </div>
        </div>
    );
};

export default AdminUsersPage;
