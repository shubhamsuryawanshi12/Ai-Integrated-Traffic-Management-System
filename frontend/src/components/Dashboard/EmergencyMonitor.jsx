import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const AlertCard = ({ alert }) => (
    <motion.div
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: -100, opacity: 0 }}
        className={`mb-4 p-4 rounded-xl border-l-4 glass-card animate-emergency ${alert.status === 'PREEMPTING' ? 'border-orange-500' : 'border-red-500'
            }`}
    >
        <div className="flex justify-between items-start mb-2">
            <span className="text-[10px] font-black uppercase tracking-widest text-orange-400">🚨 Emergency Alert</span>
            <span className="text-[10px] font-mono text-slate-500">
                {new Date(alert.timestamp).toLocaleTimeString()}
            </span>
        </div>
        <h4 className="text-white font-bold text-sm mb-1">{alert.vehicle || 'Emergency Vehicle'} detected</h4>
        <div className="flex items-center gap-2">
            <div className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] font-bold text-slate-300 uppercase">
                {alert.intersection || 'Unknown INT'}
            </div>
            <span className="text-[10px] text-slate-400 font-medium">ETA: {alert.eta_seconds || '—'}s</span>
        </div>
    </motion.div>
);

export default function EmergencyMonitor({ alerts = [] }) {
    return (
        <div className="w-80 flex flex-col h-full pr-6 border-r border-slate-800/50">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Active Alerts</h3>
                <span className="px-2 py-0.5 rounded-full bg-red-500/10 text-red-500 text-[10px] font-bold border border-red-500/20">
                    {alerts.length} LIVE
                </span>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar">
                <AnimatePresence>
                    {alerts.map((alert, idx) => (
                        <AlertCard key={alert.id || idx} alert={alert} />
                    ))}
                    {alerts.length === 0 && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex flex-col items-center justify-center h-40 border-2 border-dashed border-slate-800/50 rounded-2xl"
                        >
                            <span className="text-3xl mb-2 opacity-20">🛡️</span>
                            <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">Network Secure</span>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <div className="mt-6 p-4 glass-card rounded-2xl">
                <div className="flex items-center gap-3 mb-2">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                    <span className="text-[10px] font-black uppercase text-slate-400">Preemption System</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed italic">
                    AI agent is currently monitoring audio and visual feeds for siren signatures.
                </p>
            </div>
        </div>
    );
}
