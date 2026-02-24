import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';

/* ── colour constants ───────────────────────────────────── */
const PHASE_COLORS = {
    green: '#22c55e',
    yellow: '#eab308',
    red: '#ef4444',
};

/* ── reusable inline-style helpers (matches Dashboard.jsx) ── */
const cardStyle = {
    backgroundColor: '#1e293b',
    borderRadius: '12px',
    border: '1px solid #334155',
    padding: '24px',
    transition: 'box-shadow 0.3s ease, transform 0.3s ease',
};

/* ── small sub-components ────────────────────────────────── */

function PhaseDot({ phase }) {
    const color = PHASE_COLORS[phase] || '#94a3b8';
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
                style={{
                    width: '14px',
                    height: '14px',
                    borderRadius: '50%',
                    backgroundColor: color,
                    boxShadow: `0 0 12px ${color}`,
                    transition: 'background-color 0.4s ease, box-shadow 0.4s ease',
                }}
            />
            <span
                style={{
                    color: color,
                    fontWeight: 700,
                    fontSize: '14px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                }}
            >
                {phase}
            </span>
        </div>
    );
}

function MetricRow({ label, value, unit }) {
    return (
        <div
            style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 0',
                borderBottom: '1px solid rgba(51,65,85,0.5)',
            }}
        >
            <span style={{ color: '#94a3b8', fontSize: '13px' }}>{label}</span>
            <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: '15px' }}>
                {value}
                {unit && (
                    <span style={{ color: '#64748b', fontSize: '12px', marginLeft: '4px' }}>
                        {unit}
                    </span>
                )}
            </span>
        </div>
    );
}

function IntersectionCard({ data }) {
    const phase = data.current_status?.phase || 'red';
    const vehicleCount = data.traffic_data?.vehicle_count ?? 0;
    const avgWait = data.traffic_data?.average_wait_time ?? 0;
    const avgSpeed = data.traffic_data?.avg_speed ?? 0;
    // derive queue length from vehicle count, capped 0-20
    const queueLength = Math.min(20, Math.max(0, Math.round(vehicleCount * 0.4)));

    return (
        <div
            style={{
                ...cardStyle,
                position: 'relative',
                overflow: 'hidden',
            }}
            className="hover-glow"
        >
            {/* top accent bar */}
            <div
                style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '3px',
                    background: PHASE_COLORS[phase] || '#94a3b8',
                    transition: 'background 0.4s ease',
                }}
            />

            {/* header */}
            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '16px',
                }}
            >
                <div>
                    <h3
                        style={{
                            margin: 0,
                            fontSize: '18px',
                            fontWeight: 700,
                            color: '#f1f5f9',
                        }}
                    >
                        {data.name || `Signal ${data.id}`}
                    </h3>
                    <span style={{ color: '#64748b', fontSize: '12px' }}>{data.id}</span>
                </div>
                <PhaseDot phase={phase} />
            </div>

            {/* metrics */}
            <MetricRow label="Vehicles" value={vehicleCount} />
            <MetricRow label="Avg Wait" value={avgWait.toFixed(1)} unit="s" />
            <MetricRow label="Avg Speed" value={avgSpeed.toFixed(1)} unit="m/s" />
            <MetricRow label="Queue Length" value={queueLength} unit="veh" />
        </div>
    );
}

function StatusBadge({ connected }) {
    const color = connected ? '#22c55e' : '#ef4444';
    const label = connected ? 'LIVE' : 'DISCONNECTED';
    return (
        <span
            style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                backgroundColor: `${color}18`,
                color: color,
                padding: '4px 12px',
                borderRadius: '999px',
                fontSize: '12px',
                fontWeight: 700,
                letterSpacing: '0.05em',
                border: `1px solid ${color}40`,
            }}
        >
            <span
                style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: color,
                    boxShadow: `0 0 8px ${color}`,
                    display: 'inline-block',
                }}
            />
            {label}
        </span>
    );
}

/* ── main component ──────────────────────────────────────── */

export default function MockDataViewer() {
    const [intersections, setIntersections] = useState([]);
    const [snapshot, setSnapshot] = useState(null);
    const [connected, setConnected] = useState(false);
    const socketRef = useRef(null);

    useEffect(() => {
        const socket = io('http://localhost:8000', {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: Infinity,
        });
        socketRef.current = socket;

        socket.on('connect', () => setConnected(true));
        socket.on('disconnect', () => setConnected(false));

        socket.on('traffic_update', (data) => {
            if (data.intersections) setIntersections(data.intersections);
            if (data.snapshot) setSnapshot(data.snapshot);
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    /* ── derived values ─── */
    const avgQueueLength = snapshot?.avg_queue_length ?? '—';
    const lastUpdated = snapshot?.timestamp
        ? new Date(snapshot.timestamp).toLocaleTimeString()
        : '—';

    /* ── render ─── */
    return (
        <div
            style={{
                backgroundColor: '#0f172a',
                minHeight: '100vh',
                color: '#fff',
                padding: '24px 28px',
                fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
            }}
        >
            {/* ─── Disconnected banner ─── */}
            {!connected && (
                <div
                    style={{
                        backgroundColor: 'rgba(239, 68, 68, 0.15)',
                        border: '1px solid #ef4444',
                        borderRadius: '10px',
                        padding: '12px 20px',
                        marginBottom: '20px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        animation: 'pulse 2s infinite',
                    }}
                >
                    <span style={{ fontSize: '20px' }}>⚠️</span>
                    <span style={{ color: '#fca5a5', fontWeight: 600, fontSize: '14px' }}>
                        Socket disconnected — waiting for backend on{' '}
                        <code
                            style={{
                                backgroundColor: 'rgba(239,68,68,0.2)',
                                padding: '2px 6px',
                                borderRadius: '4px',
                            }}
                        >
                            localhost:8000
                        </code>
                    </span>
                </div>
            )}

            {/* ─── Header ─── */}
            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '28px',
                    flexWrap: 'wrap',
                    gap: '16px',
                }}
            >
                <div>
                    <h1
                        style={{
                            fontSize: '42px',
                            margin: 0,
                            background: 'linear-gradient(to right, #3b82f6, #8b5cf6)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            fontWeight: 800,
                        }}
                    >
                        Mock Simulation Viewer
                    </h1>
                    <p style={{ color: '#94a3b8', margin: '6px 0 0' }}>
                        SUMO Environment — Real-time mock data feed
                    </p>
                </div>
                <StatusBadge connected={connected} />
            </div>

            {/* ─── System Metrics Bar ─── */}
            <div
                style={{
                    ...cardStyle,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '24px',
                    flexWrap: 'wrap',
                    gap: '16px',
                    background:
                        'linear-gradient(135deg, rgba(30,41,59,1) 0%, rgba(30,41,59,0.85) 100%)',
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
                    {/* avg queue */}
                    <div>
                        <span style={{ color: '#64748b', fontSize: '12px', display: 'block' }}>
                            Avg Queue Length
                        </span>
                        <span
                            style={{
                                color: '#f1f5f9',
                                fontSize: '28px',
                                fontWeight: 700,
                            }}
                        >
                            {typeof avgQueueLength === 'number'
                                ? avgQueueLength.toFixed(1)
                                : avgQueueLength}
                        </span>
                        <span style={{ color: '#64748b', fontSize: '12px', marginLeft: '4px' }}>
                            vehicles
                        </span>
                    </div>

                    {/* divider */}
                    <div
                        style={{
                            width: '1px',
                            height: '40px',
                            backgroundColor: '#334155',
                        }}
                    />

                    {/* last updated */}
                    <div>
                        <span style={{ color: '#64748b', fontSize: '12px', display: 'block' }}>
                            Last Updated
                        </span>
                        <span style={{ color: '#e2e8f0', fontSize: '18px', fontWeight: 600 }}>
                            {lastUpdated}
                        </span>
                    </div>
                </div>

                <StatusBadge connected={connected} />
            </div>

            {/* ─── Intersection Cards — 2×2 grid ─── */}
            <h2
                style={{
                    fontSize: '20px',
                    color: '#f1f5f9',
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                }}
            >
                🚦 Intersections
                <span
                    style={{
                        fontSize: '12px',
                        color: '#3b82f6',
                        backgroundColor: 'rgba(59,130,246,0.1)',
                        padding: '4px 10px',
                        borderRadius: '6px',
                    }}
                >
                    {intersections.length} active
                </span>
            </h2>

            <div
                style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '20px',
                    marginBottom: '28px',
                }}
            >
                {(intersections.length > 0 ? intersections : placeholderIntersections).map(
                    (int) => (
                        <IntersectionCard key={int.id} data={int} />
                    ),
                )}
            </div>

            {/* ─── RL Agent Info Panel ─── */}
            <div
                style={{
                    ...cardStyle,
                    background:
                        'linear-gradient(135deg, rgba(30,41,59,1) 0%, rgba(15,23,42,1) 100%)',
                }}
            >
                <h2
                    style={{
                        fontSize: '20px',
                        color: '#f1f5f9',
                        margin: '0 0 20px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                    }}
                >
                    🤖 RL Agent Info
                    <span
                        style={{
                            fontSize: '12px',
                            color: '#eab308',
                            backgroundColor: 'rgba(234,179,8,0.1)',
                            padding: '4px 10px',
                            borderRadius: '6px',
                            border: '1px solid rgba(234,179,8,0.25)',
                        }}
                    >
                        Dummy Mode
                    </span>
                </h2>

                <div
                    style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                        gap: '16px',
                    }}
                >
                    <InfoTile
                        label="Current Mode"
                        value="Dummy (random actions)"
                        icon="🎲"
                    />
                    <InfoTile
                        label="Action Space"
                        value="Green / Yellow / Red / Extended Green"
                        icon="🎯"
                    />
                    <InfoTile
                        label="Reward Function"
                        value="−(total_waiting_time + 10 × stopped_vehicles)"
                        icon="📐"
                        mono
                    />
                    <InfoTile
                        label="State Vector Size"
                        value="32 features"
                        icon="📊"
                    />
                </div>
            </div>
        </div>
    );
}

/* ── static helper ───────────────────────────────────────── */

function InfoTile({ label, value, icon, mono }) {
    return (
        <div
            style={{
                backgroundColor: 'rgba(15,23,42,0.6)',
                border: '1px solid #334155',
                borderRadius: '10px',
                padding: '16px',
            }}
        >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '18px' }}>{icon}</span>
                <span style={{ color: '#64748b', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    {label}
                </span>
            </div>
            <span
                style={{
                    color: '#e2e8f0',
                    fontSize: '14px',
                    fontWeight: 600,
                    fontFamily: mono
                        ? '"Fira Code", "Cascadia Code", monospace'
                        : 'inherit',
                }}
            >
                {value}
            </span>
        </div>
    );
}

/* placeholder cards shown before first WebSocket message arrives */
const placeholderIntersections = [
    {
        id: 'INT_1',
        name: 'Signal INT_1',
        current_status: { phase: 'green' },
        traffic_data: { vehicle_count: 0, average_wait_time: 0, avg_speed: 0 },
    },
    {
        id: 'INT_2',
        name: 'Signal INT_2',
        current_status: { phase: 'red' },
        traffic_data: { vehicle_count: 0, average_wait_time: 0, avg_speed: 0 },
    },
    {
        id: 'INT_3',
        name: 'Signal INT_3',
        current_status: { phase: 'yellow' },
        traffic_data: { vehicle_count: 0, average_wait_time: 0, avg_speed: 0 },
    },
    {
        id: 'INT_4',
        name: 'Signal INT_4',
        current_status: { phase: 'green' },
        traffic_data: { vehicle_count: 0, average_wait_time: 0, avg_speed: 0 },
    },
];
