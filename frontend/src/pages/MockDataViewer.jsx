import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTrafficSocket } from '../hooks/useTrafficSocket';

// Components
import GlobalMetricsBar from '../components/Dashboard/GlobalMetricsBar';
import EmergencyMonitor from '../components/Dashboard/EmergencyMonitor';
import EcoImpactCard from '../components/Dashboard/EcoImpactCard';
import IntersectionCanvas from '../components/Simulation/IntersectionCanvas';

function ConnectionStatus({ connected }) {
    return (
        <div className={`fixed top-6 right-8 z-50 flex items-center gap-3 px-4 py-2 rounded-full glass-panel border ${connected ? 'border-green-500/20' : 'border-red-500/20'}`}>
            <div className={`w-2.5 h-2.5 rounded-full ${connected ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' : 'bg-red-500 animate-pulse'}`} />
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-300">
                {connected ? 'Syncing (100ms)' : 'Network Lost'}
            </span>
        </div>
    );
}

export default function MockDataViewer() {
    const { intersections, snapshot, emergencyAlerts, connected } = useTrafficSocket();

    // Intersection grid layout (smaller cards below the main canvas)
    const sortedIntersections = useMemo(() =>
        [...intersections].sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true })),
        [intersections]
    );

    return (
        <div className="min-h-screen bg-[#020617] text-slate-100 font-sans selection:bg-blue-500/30">
            <ConnectionStatus connected={connected} />

            <main className="max-w-[1700px] mx-auto p-8">
                {/* ─── Top Stats Ribbon ─── */}
                <GlobalMetricsBar snapshot={snapshot} intersections={intersections} />

                <div className="flex gap-8 items-stretch h-[calc(100vh-230px)]">

                    {/* ─── Left: Emergency Monitor ─── */}
                    <EmergencyMonitor alerts={emergencyAlerts} />

                    {/* ─── Center: The Command Canvas ─── */}
                    <div className="flex-1 flex flex-col gap-8 overflow-hidden">
                        <motion.div
                            layout
                            className="flex-1 min-h-0"
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                        >
                            <IntersectionCanvas intersections={intersections} />
                        </motion.div>

                        {/* ─── Lower: Detailed Intersection Grid ─── */}
                        <div className="h-64 grid grid-cols-4 gap-4 overflow-y-auto custom-scrollbar pr-2">
                            <AnimatePresence mode="popLayout">
                                {sortedIntersections.map((int) => (
                                    <motion.div
                                        key={int.id}
                                        layout
                                        initial={{ opacity: 0, scale: 0.8 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.8 }}
                                        className="glass-card p-5 rounded-2xl relative overflow-hidden"
                                    >
                                        <div className="absolute top-0 right-0 w-16 h-16 bg-blue-500/5 blur-2xl rounded-full" />

                                        <div className="flex justify-between items-start mb-4">
                                            <div>
                                                <h4 className="text-white font-bold text-sm tracking-tight">{int.name}</h4>
                                                <span className="text-[10px] text-slate-500 font-mono">{int.id}</span>
                                            </div>
                                            <div className={`w-2.5 h-2.5 rounded-full ${int.current_status?.phase === 'green' ? 'bg-green-500' :
                                                (int.current_status?.phase === 'yellow' ? 'bg-yellow-500' : 'bg-red-500')
                                                } shadow-lg`} />
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="flex flex-col">
                                                <span className="text-[9px] uppercase text-slate-500 font-black">Vehicles</span>
                                                <span className="text-lg font-bold text-slate-200 tabular-nums">{int.traffic_data?.vehicle_count || 0}</span>
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-[9px] uppercase text-slate-500 font-black">Wait Time</span>
                                                <span className="text-lg font-bold text-slate-200 tabular-nums">{(int.traffic_data?.average_wait_time || 0).toFixed(1)}s</span>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                            {intersections.length === 0 && (
                                <div className="col-span-4 flex items-center justify-center h-full glass-card rounded-2xl border-dashed border-2 border-slate-800">
                                    <span className="text-slate-600 font-black uppercase tracking-[0.3em] text-[10px]">Awaiting Sensor Calibration...</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* ─── Right: Environmental Insights ─── */}
                    <div className="w-80 flex flex-col gap-8">
                        <EcoImpactCard snapshot={snapshot} />

                        <div className="flex-1 glass-panel rounded-2xl p-6 relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-4 transform transition-transform group-hover:scale-125">🤖</div>
                            <h3 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-4">RL Agent Active</h3>
                            <div className="space-y-4">
                                <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-700/30">
                                    <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Last Action</span>
                                    <span className="text-sm font-bold text-blue-400 font-mono">ADAPTIVE_PHASE_SHIFT</span>
                                </div>
                                <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-700/30">
                                    <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">State Vector</span>
                                    <span className="text-sm font-bold text-slate-300 font-mono tabular-nums">32-D Tensor</span>
                                </div>
                                <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-700/30">
                                    <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Confidence</span>
                                    <div className="flex items-center gap-3">
                                        <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                            <div className="bg-blue-500 h-full w-[94%]" />
                                        </div>
                                        <span className="text-xs font-bold text-slate-400">94%</span>
                                    </div>
                                </div>
                            </div>

                            <div className="absolute bottom-6 left-6 right-6">
                                <button className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 shadow-[0_0_20px_rgba(37,99,235,0.4)]">
                                    Override Control
                                </button>
                            </div>
                        </div>
                    </div>

                </div>
            </main>
        </div>
    );
}
