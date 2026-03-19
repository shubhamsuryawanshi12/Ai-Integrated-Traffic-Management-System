import React from 'react';
import { motion } from 'framer-motion';

const MetricItem = ({ label, value, unit, icon, trend }) => (
    <div className="flex flex-col px-6 py-2 border-r border-slate-700/50 last:border-0">
        <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">{icon}</span>
            <span className="text-[10px] uppercase tracking-widest text-slate-400 font-bold">{label}</span>
        </div>
        <div className="flex items-baseline gap-1">
            <span className="text-2xl font-black text-white tabular-nums">{value}</span>
            <span className="text-xs text-slate-500 font-medium">{unit}</span>
            {trend && (
                <span className={`ml-2 text-[10px] font-bold ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
                </span>
            )}
        </div>
    </div>
);

export default function GlobalMetricsBar({ snapshot, intersections }) {
    const activeVehicles = intersections.reduce((acc, int) => acc + (int.traffic_data?.vehicle_count || 0), 0);
    const avgDelay = snapshot?.avg_queue_length?.toFixed(1) || '0.0';
    const co2Saved = snapshot?.co2_saved_kg?.toFixed(2) || '0.00';

    return (
        <motion.div
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="w-full glass-panel h-20 flex items-center mb-6 rounded-xl overflow-hidden"
        >
            <div className="px-8 flex items-center gap-3 border-r border-slate-700/50 h-full bg-slate-900/40">
                <div className="w-3 h-3 rounded-full bg-green-500 shadow-[0_0_12px_#22c55e] animate-pulse" />
                <span className="text-sm font-black tracking-tighter text-white">SYSTEM LIVE</span>
            </div>

            <div className="flex flex-1 items-center">
                <MetricItem
                    label="Active Vehicles"
                    value={activeVehicles}
                    unit="VEH"
                    icon="🚗"
                />
                <MetricItem
                    label="Network Delay"
                    value={avgDelay}
                    unit="SEC"
                    icon="⏳"
                    trend={-12}
                />
                <MetricItem
                    label="CO2 Optimized"
                    value={co2Saved}
                    unit="KG"
                    icon="🌿"
                    trend={+8}
                />
                <MetricItem
                    label="Throughput"
                    value={Math.round(activeVehicles * 1.5)}
                    unit="V/H"
                    icon="⚡"
                />
            </div>

            <div className="px-8 flex flex-col items-end">
                <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Local Time</span>
                <span className="text-lg font-mono font-bold text-slate-300">
                    {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
            </div>
        </motion.div>
    );
}
