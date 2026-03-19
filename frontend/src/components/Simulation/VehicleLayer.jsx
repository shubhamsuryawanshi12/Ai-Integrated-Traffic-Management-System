import React, { useEffect, useState } from 'react';

const VEHICLE_TYPES = {
    car: { width: 12, height: 6, color: '#3b82f6' },
    bus: { width: 18, height: 7, color: '#8b5cf6' },
    emergency: { width: 14, height: 7, color: '#f97316' }
};

const Vehicle = ({ type, x, y, rotation, isEmergency }) => {
    const specs = VEHICLE_TYPES[type] || VEHICLE_TYPES.car;

    return (
        <div
            className={`absolute transition-all duration-[1200ms] ease-linear ${isEmergency ? 'animate-emergency' : ''}`}
            style={{
                left: `${x}%`,
                top: `${y}%`,
                width: specs.width,
                height: specs.height,
                backgroundColor: specs.color,
                borderRadius: '2px',
                boxShadow: `0 0 8px ${specs.color}40`,
                transform: `translate(-50%, -50%) rotate(${rotation}deg)`
            }}
        >
            <div className="absolute top-0.5 right-0.5 w-1/4 h-3/4 bg-white/30 rounded-full" />
            <div className="absolute left-0 top-0.5 w-[2px] h-1 bg-red-500/80" />
            <div className="absolute left-0 bottom-0.5 w-[2px] h-1 bg-red-500/80" />
        </div>
    );
};

/**
 * Lane-based vehicle positioning to prevent overlap/intersection.
 *
 * For each intersection, vehicles are distributed into 4 approach directions (N, S, E, W).
 * Each direction has multiple lanes so vehicles don't stack on the same axis.
 * Vehicles are queued along their approach direction with proper spacing
 * that accounts for actual vehicle length (in percentage units).
 */
function computeVehiclePositions(intersections, size) {
    const vehicles = [];

    // Approximate vehicle length in % space. At a typical canvas width,
    // 14px ≈ 1.2% of canvas — we use a generous spacing of 1.8% to avoid any overlap.
    const VEHICLE_SPACING = 1.8;  // % gap between vehicles in the queue
    const LANE_WIDTH = 1.2;       // % offset between lanes (perpendicular to travel)
    const MIN_OFFSET = 4;         // % min distance from intersection center

    intersections.forEach((int, idx) => {
        const centerX = ((idx % size) + 0.5) * (100 / size);
        const centerY = (Math.floor(idx / size) + 0.5) * (100 / size);
        const totalCount = Math.min(16, Math.max(0, int.traffic_data?.vehicle_count || 0));
        const phase = int.current_status?.phase || 'red';

        // Distribute vehicles across 4 directions
        const directionQueues = { N: [], S: [], E: [], W: [] };
        const directions = ['N', 'S', 'E', 'W'];

        for (let i = 0; i < totalCount; i++) {
            const dir = directions[i % 4];
            const vehicleType = i === 0 && int.name?.includes('🚨')
                ? 'emergency'
                : (i % 5 === 0 ? 'bus' : 'car');
            directionQueues[dir].push({
                type: vehicleType,
                isEmergency: i === 0 && int.name?.includes('🚨'),
                globalIndex: i
            });
        }

        // Max 2 lanes per direction to keep it clean
        const LANES_PER_DIR = 2;

        for (const dir of directions) {
            const queue = directionQueues[dir];
            if (queue.length === 0) continue;

            queue.forEach((veh, queueIdx) => {
                const lane = queueIdx % LANES_PER_DIR;           // which lane (0 or 1)
                const posInLane = Math.floor(queueIdx / LANES_PER_DIR); // position along the lane

                // Distance from center along the approach direction
                const distFromCenter = MIN_OFFSET + posInLane * VEHICLE_SPACING;

                // Green-phase adjustment: vehicles start moving through
                const greenShift = phase === 'green' ? 1.5 : 0;

                // Lane offset: shift perpendicular to travel direction
                // Center the lanes: for 2 lanes, offsets are -0.6 and +0.6
                const laneOffset = (lane - (LANES_PER_DIR - 1) / 2) * LANE_WIDTH;

                let x, y, rot;

                switch (dir) {
                    case 'N': // approaching from north (above), traveling south
                        x = centerX + laneOffset;
                        y = centerY - distFromCenter + greenShift;
                        rot = 90;
                        break;
                    case 'S': // approaching from south (below), traveling north
                        x = centerX - laneOffset; // mirror lanes for opposite direction
                        y = centerY + distFromCenter - greenShift;
                        rot = 270;
                        break;
                    case 'E': // approaching from east (right), traveling west
                        x = centerX + distFromCenter - greenShift;
                        y = centerY + laneOffset;
                        rot = 180;
                        break;
                    case 'W': // approaching from west (left), traveling east
                        x = centerX - distFromCenter + greenShift;
                        y = centerY - laneOffset; // mirror lanes for opposite direction
                        rot = 0;
                        break;
                    default:
                        x = centerX;
                        y = centerY;
                        rot = 0;
                }

                vehicles.push({
                    id: `${int.id}-${dir}-${queueIdx}`,
                    x, y,
                    rotation: rot,
                    type: veh.type,
                    isEmergency: veh.isEmergency,
                });
            });
        }
    });

    return vehicles;
}

export default function VehicleLayer({ intersections }) {
    const [vehicles, setVehicles] = useState([]);
    const size = Math.ceil(Math.sqrt(intersections.length || 1));

    useEffect(() => {
        setVehicles(computeVehiclePositions(intersections, size));
    }, [intersections, size]);

    return (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
            {vehicles.map(v => (
                <Vehicle key={v.id} {...v} />
            ))}
        </div>
    );
}
