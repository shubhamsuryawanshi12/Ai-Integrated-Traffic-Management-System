import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const CommissionPage = () => {
    const navigate = useNavigate();
    const [percentage, setPercentage] = useState(10);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchComm = async () => {
            try {
                const res = await api.get('/parking/commission');
                setPercentage(res.data.percentage);
            } catch (err) {
                console.error(err);
            }
        };
        fetchComm();
    }, []);

    const handleUpdate = async () => {
        if (percentage < 0 || percentage > 100) {
            alert("Commission must be between 0 and 100");
            return;
        }
        setLoading(true);
        try {
            await api.put(`/parking/commission?percentage=${percentage}`);
            alert('Commission percentage successfully updated!');
        } catch (err) {
            alert('Failed to update commission.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: '24px', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
                 <div style={{ padding: '20px', borderRadius: '16px', backgroundColor: '#1e293b', border: '1px solid #334155', display: 'flex', gap: '16px', marginBottom: '24px' }}>
                     <button onClick={() => navigate('/admin/revenue')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Revenue Dashboard</button>
                     <button onClick={() => navigate('/admin/parking/approvals')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Pending Approvals</button>
                     <button onClick={() => navigate('/admin/commission')} style={{ backgroundColor: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>Commission Setup</button>
                     <button onClick={() => navigate('/admin/users')} style={{ backgroundColor: 'transparent', color: '#94a3b8', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>All Users</button>
                </div>

                <div style={{ backgroundColor: '#1e293b', padding: '32px', borderRadius: '16px', border: '1px solid #334155', maxWidth: '500px' }}>
                    <h2 style={{ marginTop: 0 }}>Global Platform Fee</h2>
                    <p style={{ color: '#94a3b8', marginBottom: '32px', fontSize: '14px' }}>
                        This is the percentage of every booking revenue that goes directly into the city administrative accounts. The remainder natively goes to the parking zone owner.
                    </p>

                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Commission Percentage (%)</label>
                        <div style={{ display: 'flex', gap: '12px' }}>
                            <input 
                                type="number" 
                                min="0" 
                                max="100" 
                                value={percentage} 
                                onChange={e => setPercentage(parseFloat(e.target.value))} 
                                style={{ flex: 1, padding: '16px', fontSize: '18px', borderRadius: '12px', backgroundColor: '#0f172a', color: 'white', border: '1px solid #475569' }}
                            />
                            <button 
                                onClick={handleUpdate} 
                                disabled={loading}
                                style={{ padding: '0 24px', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '12px', fontWeight: 'bold', fontSize: '16px', cursor: 'pointer' }}
                            >
                                {loading ? 'Saving...' : 'Save Rule'}
                            </button>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default CommissionPage;
