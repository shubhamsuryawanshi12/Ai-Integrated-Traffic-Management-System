// PCU-MARL++ Dashboard JavaScript

// Socket connection
const socket = io();
let isRunning = false;
let rewardsChart = null;
let rewardHistory = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initGridMap();
    initChart();
    setupEventListeners();
    connectSocket();
});

function initGridMap() {
    const gridMap = document.getElementById('grid-map');
    gridMap.innerHTML = '';

    // Create 12 junction nodes (3x4 grid)
    for (let i = 0; i < 12; i++) {
        const node = document.createElement('div');
        node.className = 'junction-node';
        node.id = `junction-${i}`;

        const phaseIndicator = document.createElement('div');
        phaseIndicator.className = 'phase-indicator phase-0';
        node.appendChild(phaseIndicator);

        const idSpan = document.createElement('span');
        idSpan.className = 'junction-id';
        idSpan.textContent = i;
        node.appendChild(idSpan);

        const queueSpan = document.createElement('span');
        queueSpan.className = 'queue-value';
        queueSpan.textContent = '0.0 PCU';
        node.appendChild(queueSpan);

        gridMap.appendChild(node);
    }
}

function initChart() {
    const ctx = document.getElementById('rewards-chart').getContext('2d');

    rewardsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Total Reward',
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8' }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                },
                y: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                }
            }
        }
    });
}

function setupEventListeners() {
    document.getElementById('start-btn').addEventListener('click', startSimulation);
    document.getElementById('stop-btn').addEventListener('click', stopSimulation);
    document.getElementById('reset-btn').addEventListener('click', resetSimulation);
}

function connectSocket() {
    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('connected', (data) => {
        console.log('Server confirmed connection:', data);
    });

    socket.on('state_update', (state) => {
        updateDashboard(state);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
    });
}

function updateDashboard(state) {
    // Update step/episode
    document.getElementById('step-count').textContent = state.step || 0;
    document.getElementById('episode-count').textContent = state.episode || 0;

    // Update weather
    const rain = state.weather?.rain_intensity || 0;
    document.getElementById('rain-value').textContent = rain.toFixed(2);
    document.getElementById('rain-bar').style.width = `${rain * 100}%`;

    // Update CATC policy
    const policy = state.active_catc_policy || 'clear';
    const catcBadge = document.getElementById('catc-policy');
    catcBadge.textContent = policy;
    catcBadge.className = `badge ${policy}`;

    // Update metrics
    const metrics = state.metrics || {};
    document.getElementById('avg-delay').textContent = (metrics.avg_delay || 0).toFixed(1);
    document.getElementById('throughput').textContent = (metrics.throughput || 0).toFixed(1);
    document.getElementById('overflow-rate').textContent = ((metrics.overflow_rate || 0) * 100).toFixed(1) + '%';

    // Calculate total PCU
    let totalPcu = 0;
    if (state.junctions) {
        state.junctions.forEach(j => {
            if (j.pcu_queue) {
                totalPcu += j.pcu_queue.reduce((a, b) => a + b, 0);
            }
        });
    }
    document.getElementById('total-pcu').textContent = totalPcu.toFixed(1);

    // Update grid map
    if (state.junctions) {
        state.junctions.forEach((junction, idx) => {
            updateJunctionNode(idx, junction);
        });
    }

    // Update rewards
    if (state.rewards) {
        const totalReward = Object.values(state.rewards).reduce((a, b) => a + b, 0);
        rewardHistory.push(totalReward);

        // Keep last 50 points
        if (rewardHistory.length > 50) {
            rewardHistory.shift();
        }

        // Update chart
        rewardsChart.data.labels = rewardHistory.map((_, i) => i);
        rewardsChart.data.datasets[0].data = rewardHistory;
        rewardsChart.update('none');
    }

    // Update module status
    updateModuleStatus(state);

    // Update junction details
    updateJunctionDetails(state);
}

function updateJunctionNode(id, junction) {
    const node = document.getElementById(`junction-${id}`);
    if (!node) return;

    // Update phase indicator
    const phase = junction.phase || 0;
    const indicator = node.querySelector('.phase-indicator');
    indicator.className = `phase-indicator phase-${phase}`;

    // Update queue value
    const queue = junction.pcu_queue || [0, 0, 0, 0];
    const totalQueue = queue.reduce((a, b) => a + b, 0);
    const queueSpan = node.querySelector('.queue-value');
    queueSpan.textContent = `${totalQueue.toFixed(1)} PCU`;
}

function updateModuleStatus(state) {
    // PCU-MARL reward
    if (state.rewards) {
        const totalReward = Object.values(state.rewards).reduce((a, b) => a + b, 0);
        document.getElementById('pcu-reward').textContent = totalReward.toFixed(2);
    }

    // IDSS (mock data for now)
    document.getElementById('idss-norm').textContent = '0.64';
    document.getElementById('idss-neighbors').textContent = '3';

    // CATC
    const rain = state.weather?.rain_intensity || 0;
    let w1, w2, w3;

    if (rain < 0.15) {
        w1 = 1.0; w2 = 0.0; w3 = 0.0;
    } else if (rain < 0.45) {
        w1 = 0.0; w2 = 1.0; w3 = 0.0;
    } else {
        w1 = 0.0; w2 = 0.0; w3 = 1.0;
    }

    document.getElementById('catc-w1').textContent = w1.toFixed(2);
    document.getElementById('catc-w2').textContent = w2.toFixed(2);
    document.getElementById('catc-w3').textContent = w3.toFixed(2);

    // LAUER
    const lauerEvent = state.lauer_event || 'No active events';
    document.getElementById('lauer-status').textContent = lauerEvent !== 'No active events' ? 'Active' : 'Idle';
    document.getElementById('lauer-event').textContent = lauerEvent.substring(0, 20) + '...';
}

function updateJunctionDetails(state) {
    const container = document.getElementById('junction-details');
    container.innerHTML = '';

    if (!state.junctions) return;

    state.junctions.forEach(j => {
        const row = document.createElement('div');
        row.className = 'junction-row';

        const queue = j.pcu_queue || [0, 0, 0, 0];

        row.innerHTML = `
            <span>J${j.id}</span>
            <span>Phase ${j.phase}</span>
            <span>${queue.reduce((a, b) => a + b, 0).toFixed(1)} PCU</span>
        `;

        container.appendChild(row);
    });
}

async function startSimulation() {
    try {
        const response = await fetch('/api/start', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'started') {
            isRunning = true;
            document.getElementById('start-btn').disabled = true;
            document.getElementById('stop-btn').disabled = false;
        }
    } catch (error) {
        console.error('Failed to start:', error);
    }
}

async function stopSimulation() {
    try {
        const response = await fetch('/api/stop', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'stopped') {
            isRunning = false;
            document.getElementById('start-btn').disabled = false;
            document.getElementById('stop-btn').disabled = true;
        }
    } catch (error) {
        console.error('Failed to stop:', error);
    }
}

async function resetSimulation() {
    try {
        const response = await fetch('/api/reset', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'reset') {
            isRunning = false;
            document.getElementById('start-btn').disabled = false;
            document.getElementById('stop-btn').disabled = true;

            // Reset displays
            rewardHistory = [];
            rewardsChart.data.labels = [];
            rewardsChart.data.datasets[0].data = [];
            rewardsChart.update();
        }
    } catch (error) {
        console.error('Failed to reset:', error);
    }
}
