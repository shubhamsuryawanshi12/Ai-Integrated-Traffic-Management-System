import React from 'react';

const CATEGORY_NAMES = {
    '2w': '2-Wheeler',
    '4w_compact': '4W Compact',
    '4w_midsize': '4W Mid-Size',
    '4w_large': '4W Large',
    '4w_ev': '4W Electric'
};

const PricingSetupStep = ({ priceData, setPriceData, categories }) => {
    const activeCategories = Object.keys(categories);

    const handlePriceChange = (id, field, value) => {
        setPriceData({
            ...priceData,
            [id]: {
                ...priceData[id],
                [field]: parseFloat(value) || 0
            }
        });
    };

    return (
        <div className="space-y-6">
            <h3 className="text-lg font-semibold text-white mb-4">Set Pricing per Category</h3>

            <div className="grid gap-6">
                {activeCategories.map((catId) => (
                    <div key={catId} className="p-6 rounded-xl border border-slate-700 bg-slate-800/40">
                        <div className="flex items-center gap-3 mb-6">
                            <span className="text-xl">💰</span>
                            <h4 className="font-bold text-blue-400 capitalize">{CATEGORY_NAMES[catId]} Rate Rules</h4>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div>
                                <label className="block text-[11px] uppercase tracking-wider text-slate-400 font-bold mb-1">Hourly Rate (₹)</label>
                                <input
                                    type="number"
                                    value={priceData[catId]?.price_per_hour || ''}
                                    onChange={(e) => handlePriceChange(catId, 'price_per_hour', e.target.value)}
                                    placeholder="20"
                                    className="w-full px-4 py-2.5 rounded-lg border border-slate-600 bg-slate-900 text-white font-mono focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-[11px] uppercase tracking-wider text-slate-400 font-bold mb-1">First Hour (₹)</label>
                                <input
                                    type="number"
                                    value={priceData[catId]?.price_first_hour || ''}
                                    onChange={(e) => handlePriceChange(catId, 'price_first_hour', e.target.value)}
                                    placeholder="30"
                                    className="w-full px-4 py-2.5 rounded-lg border border-slate-600 bg-slate-900 text-white font-mono focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-[11px] uppercase tracking-wider text-slate-400 font-bold mb-1">Daily Cap (₹)</label>
                                <input
                                    type="number"
                                    value={priceData[catId]?.daily_cap || ''}
                                    onChange={(e) => handlePriceChange(catId, 'daily_cap', e.target.value)}
                                    placeholder="200"
                                    className="w-full px-4 py-2.5 rounded-lg border border-slate-600 bg-slate-900 text-white font-mono focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-[11px] uppercase tracking-wider text-slate-400 font-bold mb-1">Overnight (₹)</label>
                                <input
                                    type="number"
                                    value={priceData[catId]?.overnight_flat || ''}
                                    onChange={(e) => handlePriceChange(catId, 'overnight_flat', e.target.value)}
                                    placeholder="80"
                                    className="w-full px-4 py-2.5 rounded-lg border border-slate-600 bg-slate-900 text-white font-mono focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        </div>

                        {catId === '4w_ev' && (
                            <div className="mt-4 pt-4 border-t border-slate-700">
                                <label className="block text-[11px] uppercase tracking-wider text-blue-400 font-bold mb-1">⚡ EV Charging Add-on (₹/hr)</label>
                                <input
                                    type="number"
                                    value={priceData[catId]?.ev_charging_per_hour || ''}
                                    onChange={(e) => handlePriceChange(catId, 'ev_charging_per_hour', e.target.value)}
                                    placeholder="20"
                                    className="w-40 px-4 py-2.5 rounded-lg border border-slate-600 bg-slate-900 text-white font-mono focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PricingSetupStep;
