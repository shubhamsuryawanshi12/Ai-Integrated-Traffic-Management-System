import React from 'react';

const CategoryOccupancy = ({ data }) => {
    if (!data || !data.categories) return null;

    const categories = Object.keys(data.categories).map(key => ({
        id: key,
        ...data.categories[key]
    }));

    const getIcon = (id) => {
        switch (id) {
            case '2w': return '🛵';
            case '4w_compact': return '🚗';
            case '4w_midsize': return '🚙';
            case '4w_large': return '🚐';
            case '4w_ev': return '⚡';
            default: return '📍';
        }
    };

    const getLabel = (id) => {
        switch (id) {
            case '2w': return '2-Wheeler';
            case '4w_compact': return '4W Compact';
            case '4w_midsize': return '4W Mid-Size';
            case '4w_large': return '4W Large';
            case '4w_ev': return 'Electric 4W';
            default: return id;
        }
    };

    return (
        <div className="space-y-6">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 px-4">Live Category Distribution</h3>

            <div className="grid gap-4">
                {categories.map((cat) => (
                    <div key={cat.id} className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 hover:bg-slate-800 hover:border-slate-600 transition-all duration-300">
                        <div className="flex items-center justify-between mb-3 px-1">
                            <div className="flex items-center gap-2">
                                <span className="text-lg">{getIcon(cat.id)}</span>
                                <span className="text-sm font-bold text-slate-100">{getLabel(cat.id)}</span>
                            </div>
                            <div className="text-xs font-mono text-slate-400">
                                <span className="text-blue-400 font-bold">{cat.occupied}</span> / <span className="text-slate-200">{cat.total}</span> slots
                            </div>
                        </div>

                        <div className="relative h-2 w-full bg-slate-900 rounded-full overflow-hidden shadow-inner">
                            <div
                                className={`absolute top-0 left-0 h-full rounded-full transition-all duration-1000 ease-out ${cat.occupancy_pct > 90 ? 'bg-gradient-to-r from-red-600 to-red-400' :
                                        cat.occupancy_pct > 75 ? 'bg-gradient-to-r from-orange-600 to-orange-400' :
                                            'bg-gradient-to-r from-blue-600 to-blue-400'
                                    }`}
                                style={{ width: `${cat.occupancy_pct}%` }}
                            />
                        </div>

                        <div className="flex justify-between mt-2 px-1">
                            <span className={`text-[10px] font-black uppercase ${cat.available > 0 ? 'text-green-500' : 'text-red-500'
                                }`}>
                                {cat.available > 0 ? `${cat.available} AVAILABLE` : 'FULL'}
                            </span>
                            <span className="text-[10px] font-black text-slate-500 uppercase">
                                {cat.occupancy_pct}% OCCUPIED
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default CategoryOccupancy;
