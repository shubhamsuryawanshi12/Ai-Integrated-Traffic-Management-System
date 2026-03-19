import React from 'react';

const TYPES = [
    { id: '2w', label: '2-Wheeler', icon: '🛵' },
    { id: '4w_compact', label: 'Compact', icon: '🚗' },
    { id: '4w_midsize', label: 'Mid-Size', icon: '🚙' },
    { id: '4w_large', label: 'Large SUV', icon: '🚐' },
    { id: '4w_ev', label: 'Electric', icon: '⚡' },
];

const VehicleTypeFilter = ({ selected, onSelect }) => {
    return (
        <div className="flex overflow-x-auto gap-3 pb-2 no-scrollbar">
            {TYPES.map((type) => (
                <button
                    key={type.id}
                    onClick={() => onSelect(type.id)}
                    className={`flex-shrink-0 flex flex-col items-center gap-2 p-4 rounded-2xl border transition-all ${selected === type.id
                            ? 'bg-blue-600 border-blue-500 shadow-lg shadow-blue-500/20 scale-105'
                            : 'bg-slate-800 border-slate-700 text-slate-400'
                        }`}
                >
                    <span className="text-2xl">{type.icon}</span>
                    <span className={`text-[10px] font-black uppercase tracking-widest ${selected === type.id ? 'text-white' : 'text-slate-500'}`}>
                        {type.label}
                    </span>
                </button>
            ))}
        </div>
    );
};

export default VehicleTypeFilter;
