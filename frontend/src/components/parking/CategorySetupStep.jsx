import React from 'react';

const CATEGORIES = [
    { id: '2w', label: '2-Wheeler', icon: '🛵', desc: 'Bike / Scooter', size: '1.2m x 2.5m' },
    { id: '4w_compact', label: '4W Compact', icon: '🚗', desc: 'Hatchback / Small Car', size: '2.3m x 4.5m' },
    { id: '4w_midsize', label: '4W Mid-Size', icon: '🚙', desc: 'Sedan / Compact SUV', size: '2.5m x 5.0m' },
    { id: '4w_large', label: '4W Large', icon: '🚐', desc: 'Full-Size SUV / MUV', size: '2.8m x 5.5m' },
    { id: '4w_ev', label: '4W Electric', icon: '⚡', desc: 'Dedicated EV Charging Bay', size: '2.5m x 5.0m' },
];

const CategorySetupStep = ({ categories, setCategories, totalCapacity }) => {
    const handleToggle = (id) => {
        if (categories[id]) {
            const { [id]: removed, ...rest } = categories;
            setCategories(rest);
        } else {
            setCategories({ ...categories, [id]: { total_slots: 0, has_ev_charging: id === '4w_ev' } });
        }
    };

    const handleCountChange = (id, val) => {
        setCategories({ ...categories, [id]: { ...categories[id], total_slots: parseInt(val) || 0 } });
    };

    const assignedSlots = Object.values(categories).reduce((sum, cat) => sum + (cat.total_slots || 0), 0);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-white">Vehicle Category Setup</h3>
                <div className={`px-3 py-1 rounded-full text-xs font-bold ${assignedSlots === totalCapacity ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                    {assignedSlots} / {totalCapacity} Slots Assigned
                </div>
            </div>

            <div className="grid gap-4">
                {CATEGORIES.map((cat) => (
                    <div key={cat.id} className={`p-4 rounded-xl border transition-all ${categories[cat.id] ? 'bg-blue-600/10 border-blue-500/50' : 'bg-slate-800/50 border-slate-700'}`}>
                        <div className="flex items-center justify-between gap-4">
                            <div className="flex items-center gap-3">
                                <input 
                                    type="checkbox" 
                                    checked={!!categories[cat.id]} 
                                    onChange={() => handleToggle(cat.id)}
                                    className="w-5 h-5 rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500"
                                />
                                <div className="text-2xl">{cat.icon}</div>
                                <div>
                                    <h4 className="font-medium text-slate-200">{cat.label}</h4>
                                    <p className="text-xs text-slate-400">{cat.desc} • {cat.size}</p>
                                </div>
                            </div>

                            {categories[cat.id] && (
                                <div className="flex items-center gap-2">
                                    <label className="text-xs text-slate-400 font-medium">Slots:</label>
                                    <input 
                                        type="number" 
                                        min="1"
                                        value={categories[cat.id].total_slots}
                                        onChange={(e) => handleCountChange(cat.id, e.target.value)}
                                        className="w-20 px-2 py-1.5 rounded-lg border border-slate-600 bg-slate-900 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {assignedSlots > totalCapacity && (
                <p className="text-red-400 text-sm mt-2 font-medium">⚠️ Error: Assigned slots exceeds total capacity of {totalCapacity}.</p>
            )}
        </div>
    );
};

export default CategorySetupStep;
