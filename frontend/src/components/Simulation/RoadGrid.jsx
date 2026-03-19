import React from 'react';

export default function RoadGrid({ intersections }) {
    const size = Math.ceil(Math.sqrt(intersections.length || 1));

    return (
        <svg className="absolute inset-0 w-full h-full opacity-40">
            <defs>
                <pattern id="roadPattern" width="100" height="100" patternUnits="userSpaceOnUse">
                    <rect width="100" height="100" fill="transparent" />
                    <line x1="0" y1="50" x2="100" y2="50" stroke="#1e293b" strokeWidth="2" strokeDasharray="10,5" />
                    <line x1="50" y1="0" x2="50" y2="100" stroke="#1e293b" strokeWidth="2" strokeDasharray="10,5" />
                </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#roadPattern)" opacity="0.1" />
            {intersections.map((int, idx) => {
                const x = ((idx % size) + 0.5) * (100 / size);
                const y = (Math.floor(idx / size) + 0.5) * (100 / size);
                return (
                    <g key={`road-${int.id}`}>
                        {/* Horizontal road */}
                        <rect x="0" y={`${y - 4}%`} width="100%" height="8%" fill="#1e293b" className="opacity-50" />
                        {/* Horizontal lane divider (dashed center line) */}
                        <line
                            x1="0" y1={`${y}%`}
                            x2="100%" y2={`${y}%`}
                            stroke="#475569" strokeWidth="1" strokeDasharray="6,4" opacity="0.4"
                        />

                        {/* Vertical road */}
                        <rect x={`${x - 2}%`} y="0" width="4%" height="100%" fill="#1e293b" className="opacity-50" />
                        {/* Vertical lane divider (dashed center line) */}
                        <line
                            x1={`${x}%`} y1="0"
                            x2={`${x}%`} y2="100%"
                            stroke="#475569" strokeWidth="1" strokeDasharray="6,4" opacity="0.4"
                        />

                        {/* Intersection box */}
                        <rect x={`${x - 2.5}%`} y={`${y - 4.5}%`} width="5%" height="9%" fill="#334155" rx="4" />
                    </g>
                );
            })}
        </svg>
    );
}
