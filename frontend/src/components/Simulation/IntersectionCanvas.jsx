import React, { useMemo } from 'react';
import RoadGrid from './RoadGrid';
import VehicleLayer from './VehicleLayer';
import SignalHeadOverlay from './SignalHeadOverlay';
import FlowArrows from './FlowArrows';

export default function IntersectionCanvas({ intersections }) {
    const gridLayout = useMemo(() => {
        const size = Math.ceil(Math.sqrt(intersections.length || 1));
        return intersections.map((int, idx) => ({
            ...int,
            gridX: idx % size,
            gridY: Math.floor(idx / size),
        }));
    }, [intersections]);

    return (
        <div className="relative w-full aspect-video glass-panel rounded-3xl overflow-hidden bg-[#0a0f1e] border border-slate-800/80 shadow-2xl">
            <RoadGrid intersections={gridLayout} />
            <FlowArrows intersections={gridLayout} />
            <VehicleLayer intersections={gridLayout} />
            <div className="absolute inset-0 pointer-events-none p-12 grid gap-24"
                style={{
                    gridTemplateColumns: `repeat(${Math.ceil(Math.sqrt(intersections.length || 1))}, 1fr)`,
                    gridTemplateRows: `repeat(${Math.ceil(Math.sqrt(intersections.length || 1))}, 1fr)`
                }}>
                {gridLayout.map(int => (
                    <SignalHeadOverlay key={int.id} intersection={int} />
                ))}
            </div>
            <div className="absolute bottom-6 left-8 px-4 py-2 glass-panel rounded-lg border border-slate-700/50 flex items-center gap-3">
                <div className="flex gap-1">
                    <div className="w-2 h-4 bg-blue-500/30 border border-blue-500/50 rounded-sm" />
                    <div className="w-2 h-4 bg-blue-500/50 border border-blue-500/50 rounded-sm" />
                    <div className="w-2 h-4 bg-blue-500 border border-blue-500 rounded-sm" />
                </div>
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Live Traffic Synthesis</span>
            </div>
        </div>
    );
}
