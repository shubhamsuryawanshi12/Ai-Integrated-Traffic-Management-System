import React from 'react';

const SignalHead = ({ phase }) => {
    const isActive = (p) => phase === p;

    return (
        <div className="flex flex-col gap-1.5 p-2 bg-slate-900/90 rounded-lg border border-slate-700/50 shadow-xl backdrop-blur-md">
            <div className={`w-3.5 h-3.5 rounded-full border border-black/20 ${isActive('red') ? 'bg-red-500 shadow-[0_0_12px_#ef4444] animate-pulse-slow' : 'bg-red-900/30'}`} />
            <div className={`w-3.5 h-3.5 rounded-full border border-black/20 ${isActive('yellow') ? 'bg-yellow-500 shadow-[0_0_12px_#eab308]' : 'bg-yellow-900/30'}`} />
            <div className={`w-3.5 h-3.5 rounded-full border border-black/20 ${isActive('green') ? 'bg-green-500 shadow-[0_0_12px_#22c55e] animate-pulse-slow' : 'bg-green-900/30'}`} />
        </div>
    );
};

export default function SignalHeadOverlay({ intersection }) {
    const phase = intersection.current_status?.phase || 'red';

    return (
        <div className="flex flex-col items-center justify-center gap-4">
            <div className="flex flex-col items-center">
                <span className="text-[9px] font-black tracking-widest text-slate-500 uppercase mb-2 bg-slate-900/50 px-2 py-0.5 rounded border border-slate-800/50">
                    {intersection.id}
                </span>
                <div className="flex gap-4">
                    <SignalHead phase={phase} />
                </div>
            </div>
            {phase === 'green' && (
                <div className="px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full">
                    <span className="text-[10px] font-black text-green-500 uppercase tracking-tighter">Clearance Active</span>
                </div>
            )}
            {phase === 'emergency' && (
                <div className="px-3 py-1 bg-orange-500/10 border border-orange-500/20 rounded-full animate-emergency">
                    <span className="text-[10px] font-black text-orange-500 uppercase tracking-tighter">PREEMPTION</span>
                </div>
            )}
        </div>
    );
}
