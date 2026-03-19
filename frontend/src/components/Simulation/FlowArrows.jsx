import React from 'react';

export default function FlowArrows({ intersections }) {
    const size = Math.ceil(Math.sqrt(intersections.length || 1));

    return (
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
            {intersections.map((int, idx) => {
                const centerX = ((idx % size) + 0.5) * (100 / size);
                const centerY = (Math.floor(idx / size) + 0.5) * (100 / size);
                const count = int.traffic_data?.vehicle_count || 0;
                const weight = Math.min(8, 2 + count / 5);
                const color = count > 10 ? '#ef4444' : (count > 5 ? '#eab308' : '#22c55e');

                return (
                    <g key={`flow-${int.id}`} stroke={color} strokeWidth={weight} strokeLinecap="round" opacity="0.6">
                        <line x1={`${centerX}%`} y1={`${centerY - 15}%`} x2={`${centerX}%`} y2={`${centerY - 5}%`} strokeDasharray="5,3" />
                        <line x1={`${centerX}%`} y1={`${centerY + 15}%`} x2={`${centerX}%`} y2={`${centerY + 5}%`} strokeDasharray="5,3" />
                        <line x1={`${centerX + 15}%`} y1={`${centerY}%`} x2={`${centerX + 5}%`} y2={`${centerY}%`} strokeDasharray="5,3" />
                        <line x1={`${centerX - 15}%`} y1={`${centerY}%`} x2={`${centerX - 5}%`} y2={`${centerY}%`} strokeDasharray="5,3" />
                    </g>
                );
            })}
        </svg>
    );
}
