import React from 'react';
import CountUp from 'react-countup';
import { motion } from 'framer-motion';

export default function EcoImpactCard({ snapshot }) {
    const co2 = snapshot?.co2_saved_kg || 0;
    const trees = (co2 / 0.06).toFixed(1); // Rough conversion: 1 tree absorbs ~0.06kg CO2 per day in urban environments

    return (
        <motion.div
            whileHover={{ scale: 1.02 }}
            className="p-6 glass-panel rounded-2xl border-t-4 border-green-500/50"
        >
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-xs font-black uppercase tracking-widest text-green-400 mb-1">Eco Efficiency</h3>
                    <p className="text-[10px] text-slate-500 font-medium">Environmental impact savings since boot</p>
                </div>
                <span className="text-2xl">🌿</span>
            </div>

            <div className="mb-6">
                <div className="flex items-baseline gap-2 mb-1">
                    <span className="text-4xl font-black text-white tabular-nums">
                        <CountUp end={co2} decimals={2} duration={1} />
                    </span>
                    <span className="text-sm font-bold text-slate-500 uppercase">kg CO₂</span>
                </div>
                <div className="w-full bg-slate-800/50 h-1.5 rounded-full overflow-hidden">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(100, co2 * 10)}%` }}
                        className="bg-green-500 h-full shadow-[0_0_12px_#22c55e]"
                    />
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-800/50">
                    <span className="block text-[10px] uppercase text-slate-500 font-bold mb-1">Tree Equiv</span>
                    <span className="text-lg font-bold text-white font-mono">{trees}</span>
                </div>
                <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-800/50">
                    <span className="block text-[10px] uppercase text-slate-500 font-bold mb-1">Fuel Saved</span>
                    <span className="text-lg font-bold text-white font-mono">{(co2 / 2.31).toFixed(2)}L</span>
                </div>
            </div>

            <p className="mt-4 text-[9px] text-slate-600 leading-tight uppercase font-black tracking-tighter">
                * Real-time calculation based on actual vehicle idle reduction vs. baseline.
            </p>
        </motion.div>
    );
}
