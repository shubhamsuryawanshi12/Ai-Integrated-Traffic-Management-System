import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import CategoryOccupancy from '../../components/parking/CategoryOccupancy';

const OwnerDashboard = () => {
    const navigate = useNavigate();
    const { currentUser, switchRole } = useAuth();
    const [lotData, setLotData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboard = async () => {
            try {
                // In v2.0 we use the lot_id from the user profile
                const lotId = currentUser?.lot_id || 'LOT_DEMO_001';
                const res = await api.get(`/lot/${lotId}/availability`);
                setLotData(res.data);
            } catch (err) {
                console.error("Dashboard Load Error", err);
            } finally {
                setLoading(false);
            }
        };
        fetchDashboard();

        // Refresh every 10 seconds for "Live" feel
        const interval = setInterval(fetchDashboard, 10000);
        return () => clearInterval(interval);
    }, [currentUser]);

    if (loading) return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
    );

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 font-inter">
            {/* Header / Nav */}
            <nav className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center font-black text-xl shadow-lg shadow-blue-900/40">P</div>
                        <h1 className="text-xl font-black tracking-tight">{lotData?.lot_name || "Owner Portal"}</h1>
                        <span className="px-2 py-0.5 rounded-full bg-green-500/10 text-green-500 text-[10px] font-black uppercase tracking-widest border border-green-500/20">LIVE v2.0</span>
                    </div>

                    <div className="flex items-center gap-6">
                        <button onClick={() => navigate('/owner/add-parking')} className="hidden md:block text-xs font-bold text-blue-400 hover:text-blue-300 transition-colors uppercase tracking-widest">+ New Lot Setup</button>
                        <div className="h-8 w-px bg-slate-800 mx-2"></div>
                        <div className="flex items-center gap-3">
                            <div className="text-right hidden sm:block">
                                <p className="text-xs font-bold text-white">{currentUser?.name || "Rajesh Patil"}</p>
                                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Prime Owner</p>
                            </div>
                            <button
                                onClick={() => { switchRole('citizen'); navigate('/'); }}
                                className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center hover:bg-red-500/10 hover:border-red-500/50 transition-all group"
                            >
                                <span className="group-hover:scale-110 transition-transform">🚪</span>
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto p-8 grid lg:grid-cols-12 gap-8">
                {/* Left Side: Stats & Revenue */}
                <div className="lg:col-span-8 space-y-8">
                    {/* Hero Stats */}
                    <div className="grid sm:grid-cols-3 gap-6">
                        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 hover:border-blue-500/50 transition-all">
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Total Capacity</p>
                            <p className="text-4xl font-black text-white">{lotData?.total_capacity || 0}</p>
                            <div className="mt-4 flex items-center gap-2">
                                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-blue-500 w-full opacity-30"></div>
                                </div>
                            </div>
                        </div>
                        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 hover:border-green-500/50 transition-all">
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Available Slots</p>
                            <p className="text-4xl font-black text-green-500">{lotData?.total_available || 0}</p>
                            <p className="text-[10px] font-bold text-slate-500 mt-2">Update: Just now</p>
                        </div>
                        <div className="p-6 rounded-3xl bg-gradient-to-br from-indigo-900/40 to-slate-900 border border-indigo-500/30">
                            <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">Estimated Revenue</p>
                            <p className="text-4xl font-black text-white">₹4,820</p>
                            <span className="text-[10px] font-bold text-indigo-400 bg-indigo-400/10 px-2 py-0.5 rounded-full mt-2 inline-block">+12% vs yesterday</span>
                        </div>
                    </div>

                    {/* Main Charts / Activity Placeholder */}
                    <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 min-h-[400px]">
                        <div className="flex justify-between items-center mb-8">
                            <h2 className="text-lg font-black text-white uppercase tracking-tight">Recent Activity Log</h2>
                            <button className="text-[10px] font-bold text-slate-500 border border-slate-700 px-4 py-1.5 rounded-full hover:bg-slate-800 transition-all">Today ▼</button>
                        </div>

                        <div className="space-y-4">
                            {[
                                { time: "11:05 AM", msg: "Slot EV-002 Occupied", type: "⚡", user: "Nexon EV (MH12-TY-4421)" },
                                { time: "10:58 AM", msg: "Slot 4L-007 Vacated", type: "🚐", user: "Fortuner (MH14-PA-1002)" },
                                { time: "10:45 AM", msg: "Slot 2W-012 Booked", type: "🛵", user: "Activa (MH12-SQ-0081)" },
                                { time: "10:30 AM", msg: "Slot 4C-022 Occupied", type: "🚗", user: "Swift (MH09-AB-1234)" },
                            ].map((log, i) => (
                                <div key={i} className="flex items-center gap-4 p-4 rounded-2xl bg-slate-950/50 border border-slate-800/50 hover:border-slate-700 transition-all">
                                    <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-lg">{log.type}</div>
                                    <div className="flex-1">
                                        <p className="text-sm font-bold text-slate-200">{log.msg}</p>
                                        <p className="text-[11px] text-slate-500 font-medium">{log.user}</p>
                                    </div>
                                    <div className="text-[11px] font-mono font-bold text-slate-600">{log.time}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right Side: Category Breakdown */}
                <div className="lg:col-span-4">
                    <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 sticky top-28">
                        <CategoryOccupancy data={lotData} />

                        <div className="mt-8 pt-8 border-t border-slate-800 space-y-4">
                            <button
                                onClick={() => navigate('/owner/add-parking')}
                                className="w-full py-4 rounded-2xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-black uppercase tracking-widest text-slate-100 transition-all shadow-xl hover:shadow-blue-900/5"
                            >
                                Lot Configuration
                            </button>
                            <button className="w-full py-4 rounded-2xl bg-blue-600 hover:bg-blue-500 text-xs font-black uppercase tracking-widest text-white transition-all shadow-xl shadow-blue-900/40">
                                View Full Reports
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default OwnerDashboard;
