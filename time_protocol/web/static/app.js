/**
 * TIME Protocol - Interactive Web UI Client
 * Zero dependencies - pure vanilla JavaScript
 */

const API_BASE = '';

// ============ Utilities ============
async function fetchJSON(url, options = {}) {
    try {
        const res = await fetch(url, options);
        return await res.json();
    } catch (e) {
        console.error(`Fetch error ${url}:`, e);
        return { error: e.message };
    }
}

function shortHash(hash, len = 16) {
    return hash ? hash.substring(0, len) + '...' : '';
}

function formatTime(timestamp) {
    const d = new Date(timestamp * 1000);
    return d.toLocaleTimeString();
}

// ============ Mining Control ============
async function startMining() {
    const address = document.getElementById('miner-address').value || 'WEB_MINER';
    const result = await fetchJSON('/api/mining/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({miner_address: address})
    });
    
    showToast(`Mining started: ${result.status}`, result.status === 'STARTED' ? 'success' : 'info');
    refreshStatus();
}

async function stopMining() {
    const result = await fetchJSON('/api/mining/stop', {method: 'POST'});
    showToast(`Mining stopped: ${result.blocks_mined} blocks`, 'info');
    refreshStatus();
}

async function mineOneBlock() {
    const address = document.getElementById('miner-address').value || 'WEB_MINER';
    const result = await fetchJSON('/api/mine', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({miner_address: address})
    });
    
    if (result.status === 'SUCCESS') {
        showToast(`Block #${result.block.index} mined!`, 'success');
    } else {
        showToast(`Error: ${result.error || 'unknown'}`, 'error');
    }
    refreshStatus();
}

// ============ Transaction ============
async function sendTransaction(event) {
    event.preventDefault();
    const form = event.target;
    const from = form.from_address.value.trim();
    const to = form.to_address.value.trim();
    const amount = parseFloat(form.amount.value);
    
    if (!from || !to || !amount || amount <= 0) {
        showToast('Please fill all fields correctly', 'error');
        return;
    }
    
    const result = await fetchJSON('/api/tx/send', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({from, to, amount})
    });
    
    if (result.status === 'SUCCESS') {
        showToast(`TX sent: ${shortHash(result.txid)}`, 'success');
        form.reset();
    } else {
        showToast(`Error: ${result.error || 'unknown'}`, 'error');
    }
    refreshStatus();
}

// ============ Status Refresh ============
async function refreshStatus() {
    const status = await fetchJSON('/api/status');
    if (status.error) return;
    
    // Mining badge
    const badge = document.getElementById('mining-badge');
    if (status.mining.running) {
        badge.className = 'badge badge-running';
        badge.textContent = '⛏ MINING ACTIVE';
    } else {
        badge.className = 'badge badge-stopped';
        badge.textContent = '⏹ MINING STOPPED';
    }
    
    // Stats
    document.getElementById('stat-height').textContent = status.height;
    document.getElementById('stat-difficulty').textContent = status.current_difficulty;
    document.getElementById('stat-blocks-mined').textContent = status.mining.blocks_mined || 0;
    document.getElementById('stat-hashrate').textContent = status.estimated_hashrate || '0 H/s';
    document.getElementById('stat-avg-time').textContent = status.avg_block_time + 's';
    document.getElementById('stat-utxos').textContent = status.total_utxos;
    
    // Blocks table
    await refreshBlocks();
}

async function refreshBlocks() {
    const data = await fetchJSON('/api/blocks?limit=10');
    if (!data.blocks) return;
    
    const tbody = document.getElementById('blocks-tbody');
    tbody.innerHTML = data.blocks.map(b => `
        <tr>
            <td><a href="/block/${b.index}">#${b.index}</a></td>
            <td><a href="/block/${b.index}" class="hash">${shortHash(b.hash)}</a></td>
            <td>${b.difficulty}</td>
            <td>${b.time_str}</td>
            <td>${b.tx_count}</td>
            <td>${b.nonce.toLocaleString()}</td>
        </tr>
    `).join('');
}

// ============ Toast Notifications ============
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============ Auto-refresh ============
let refreshInterval = null;

function startAutoRefresh(intervalMs = 2000) {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(refreshStatus, intervalMs);
}

// ============ Init ============
document.addEventListener('DOMContentLoaded', () => {
    refreshStatus();
    startAutoRefresh(2000);
    console.log('✅ TIME Protocol Web UI loaded');
});
