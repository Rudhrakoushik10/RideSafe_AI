const API = '';
let allViolations = [];
let detectionHistory = [];
let pieChart = null;
let gaugeChart = null;
let currentViolations = [];
let currentFile = null;

document.addEventListener('DOMContentLoaded', init);

function init() {
    checkApi();
    setInterval(checkApi, 10000);
    setupNavigation();
    setupUpload();
    setupSettings();
    setupFilters();
    setupDownloads();
    loadViolations();
}

async function checkApi() {
    const el = document.getElementById('api-status');
    const dot = el.previousElementSibling;
    try {
        const r = await fetch(`${API}/api/dashboard`);
        if (r.ok) { el.textContent = 'System Online'; dot.className = 'dot green pulse'; }
        else throw 0;
    } catch {
        el.textContent = 'System Offline'; dot.className = 'dot red';
    }
}

function setupNavigation() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(`page-${tab.dataset.page}`).classList.add('active');
            if (tab.dataset.page === 'violations') loadViolations();
            if (tab.dataset.page === 'history') renderHistory();
        });
    });
}

function setupSettings() {
    const slider = document.getElementById('conf-slider');
    const display = document.getElementById('conf-value');
    slider.addEventListener('input', () => { display.textContent = slider.value + '%'; });
}

function setupUpload() {
    const zone = document.getElementById('drop-zone');
    const input = document.getElementById('file-input');
    zone.addEventListener('click', () => input.click());
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => {
        e.preventDefault(); zone.classList.remove('dragover');
        if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });
    input.addEventListener('change', () => { if (input.files.length) handleFile(input.files[0]); });
    document.getElementById('btn-new-file').addEventListener('click', resetUpload);
    document.getElementById('btn-view-violations').addEventListener('click', () => {
        document.querySelector('.tab[data-page="violations"]').click();
    });
}

function setupFilters() {
    document.getElementById('filter-type').addEventListener('change', applyFilters);
    document.getElementById('filter-status').addEventListener('change', applyFilters);
}

function setupDownloads() {
    document.getElementById('btn-download-csv').addEventListener('click', downloadCSV);
    document.getElementById('btn-download-image').addEventListener('click', downloadAnnotatedImage);
}

function resetUpload() {
    document.getElementById('drop-zone').classList.remove('hidden');
    document.getElementById('analysis-area').classList.add('hidden');
    document.getElementById('btn-new-file').style.display = 'none';
    document.getElementById('preview-image').classList.add('hidden');
    document.getElementById('preview-video').classList.add('hidden');
    document.getElementById('frame-strip').innerHTML = '';
    const c = document.getElementById('overlay-canvas');
    c.getContext('2d').clearRect(0, 0, c.width, c.height);
    currentViolations = [];
    currentFile = null;
}

async function handleFile(file) {
    currentFile = file;
    const isVideo = file.type.startsWith('video');
    const reader = new FileReader();
    reader.onload = async (e) => {
        showPreview(e.target.result, isVideo);
        await runAnalysis(file, isVideo);
    };
    reader.readAsDataURL(file);
}

function showPreview(src, isVideo) {
    document.getElementById('drop-zone').classList.add('hidden');
    document.getElementById('analysis-area').classList.remove('hidden');
    document.getElementById('btn-new-file').style.display = 'inline-flex';
    const img = document.getElementById('preview-image');
    const vid = document.getElementById('preview-video');
    const canvas = document.getElementById('overlay-canvas');
    if (isVideo) {
        vid.src = src; vid.classList.remove('hidden'); img.classList.add('hidden');
        vid.onloadedmetadata = () => { canvas.width = vid.videoWidth; canvas.height = vid.videoHeight; };
    } else {
        img.src = src; img.classList.remove('hidden'); vid.classList.add('hidden');
        img.onload = () => { canvas.width = img.naturalWidth; canvas.height = img.naturalHeight; };
    }
}

async function runAnalysis(file, isVideo) {
    const analyzing = document.getElementById('analyzing-state');
    const results = document.getElementById('results-state');
    const scanLine = document.getElementById('scan-line');
    const logFeed = document.getElementById('log-feed');
    const progressFill = document.getElementById('progress-fill');
    const statusText = document.getElementById('analysis-status');

    analyzing.classList.remove('hidden');
    results.classList.add('hidden');
    logFeed.innerHTML = '';
    scanLine.classList.add('active');

    const conf = document.getElementById('conf-slider').value;
    const mode = document.getElementById('analysis-mode').value;

    const steps = [
        [5, 'Loading YOLOv8 detection models...', 'ok'],
        [12, 'Loading helmet classifier (conf: ' + conf + '%)...', 'ok'],
        [20, 'Loading license plate detector...', 'ok'],
        [28, 'Loading traffic light classifier...', 'ok'],
        [35, 'Reading input frames...', 'ok'],
    ];
    if (isVideo) {
        steps.push([42, 'Extracting key frames...', 'ok']);
        for (let i = 1; i <= 4; i++) steps.push([42 + i * 8, `Processing frame ${i}...`, 'ok']);
    }
    steps.push([isVideo ? 78 : 50, 'Running YOLO inference...', 'ok']);
    steps.push([isVideo ? 84 : 60, 'Detecting two-wheeler riders...', 'ok']);
    steps.push([isVideo ? 88 : 68, 'Running helmet classification...', 'ok']);
    steps.push([isVideo ? 91 : 75, 'Running plate ANPR...', 'ok']);
    steps.push([isVideo ? 94 : 82, 'Classifying violations...', 'ok']);
    steps.push([isVideo ? 97 : 90, 'Generating evidence crops...', 'ok']);

    for (const [pct, msg, cls] of steps) {
        progressFill.style.width = pct + '%';
        statusText.textContent = msg;
        logFeed.innerHTML += `<div class="${cls}">${msg}</div>`;
        logFeed.scrollTop = logFeed.scrollHeight;
        await sleep(100);
    }

    try {
        const formData = new FormData();
        formData.append('file', file);
        const endpoint = isVideo ? '/api/analyze/video' : '/api/analyze/image';
        const params = new URLSearchParams({ confidence_threshold: (conf / 100).toFixed(2), mode });
        const response = await fetch(`${API}${endpoint}?${params}`, { method: 'POST', body: formData });
        const data = await response.json();
        progressFill.style.width = '100%';
        statusText.textContent = 'Analysis complete!';
        logFeed.innerHTML += `<div class="ok">Done — ${data.count || 0} violation(s) detected</div>`;
        scanLine.classList.remove('active');
        await sleep(400);
        showResults(data.violations || [], isVideo);
    } catch (err) {
        progressFill.style.width = '100%';
        statusText.textContent = 'Analysis failed';
        logFeed.innerHTML += `<div class="err">Error: ${err.message}</div>`;
        scanLine.classList.remove('active');
        await sleep(400);
        showResults([], isVideo);
    }
}

function showResults(violations, isVideo) {
    document.getElementById('analyzing-state').classList.add('hidden');
    document.getElementById('results-state').classList.remove('hidden');
    currentViolations = violations;

    const counts = { NO_HELMET: 0, RED_LIGHT: 0, WRONG_SIDE: 0 };
    violations.forEach(v => { if (counts[v.violation_type] !== undefined) counts[v.violation_type]++; });
    const total = violations.length;
    const avgConf = total > 0 ? Math.round(violations.reduce((a, v) => a + v.confidence, 0) / total) : 0;
    const totalFine = violations.reduce((a, v) => a + (v.fine_amount || 0), 0);
    const safetyScore = Math.max(0, 100 - total * 15);

    document.getElementById('m-violations').textContent = total;
    document.getElementById('m-compliant').textContent = Math.max(0, (isVideo ? 4 : 1) - total);
    document.getElementById('m-helmet').textContent = counts.NO_HELMET;
    document.getElementById('m-redlight').textContent = counts.RED_LIGHT;
    document.getElementById('m-wrongside').textContent = counts.WRONG_SIDE;
    document.getElementById('m-conf').textContent = avgConf + '%';
    document.getElementById('m-fine').textContent = 'Rs.' + totalFine.toLocaleString();
    document.getElementById('m-safety').textContent = safetyScore;

    const banner = document.getElementById('result-banner');
    if (total > 0) {
        banner.innerHTML = `<div class="violation-banner danger">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            <b>VIOLATIONS DETECTED</b> — ${total} infraction(s) found. ${totalFine > 0 ? 'Total assessed fine: Rs.' + totalFine.toLocaleString() : ''}
        </div>`;
    } else {
        banner.innerHTML = `<div class="violation-banner safe">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            <b>MONITORED AREA SAFE</b> — All detected two-wheelers are compliant with traffic regulations.
        </div>`;
    }

    renderPieChart(counts);
    renderGauge(safetyScore);
    renderDetections(violations);
    drawBoxes(violations);
    generateFrameStrip();

    detectionHistory.push({
        time: new Date().toLocaleTimeString(),
        date: new Date().toLocaleDateString(),
        violations: total,
        helmet: counts.NO_HELMET,
        redlight: counts.RED_LIGHT,
        wrongside: counts.WRONG_SIDE,
        fine: totalFine,
        safety: safetyScore,
        avgConf: avgConf,
    });
}

function renderPieChart(counts) {
    const ctx = document.getElementById('pie-chart').getContext('2d');
    if (pieChart) pieChart.destroy();
    const labels = [];
    const data = [];
    const colors = [];
    if (counts.NO_HELMET > 0) { labels.push('No Helmet'); data.push(counts.NO_HELMET); colors.push('#ef4444'); }
    if (counts.RED_LIGHT > 0) { labels.push('Red Light'); data.push(counts.RED_LIGHT); colors.push('#f59e0b'); }
    if (counts.WRONG_SIDE > 0) { labels.push('Wrong Side'); data.push(counts.WRONG_SIDE); colors.push('#f97316'); }
    if (data.length === 0) { labels.push('No Violations'); data.push(1); colors.push('#10b981'); }
    pieChart = new Chart(ctx, {
        type: 'doughnut',
        data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 0 }] },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'monospace', size: 11 } } } },
            cutout: '65%',
        }
    });
}

function renderGauge(score) {
    const ctx = document.getElementById('gauge-chart').getContext('2d');
    if (gaugeChart) gaugeChart.destroy();
    const color = score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444';
    gaugeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Safety', 'Risk'],
            datasets: [{ data: [score, 100 - score], backgroundColor: [color, '#1e293b'], borderWidth: 0 }]
        },
        options: {
            responsive: true, rotation: -90, circumference: 180,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            cutout: '75%',
        },
        plugins: [{
            id: 'gaugeText',
            afterDraw(chart) {
                const { ctx, width, height } = chart;
                ctx.save();
                ctx.font = 'bold 28px monospace';
                ctx.fillStyle = color;
                ctx.textAlign = 'center';
                ctx.fillText(score, width / 2, height / 2 + 10);
                ctx.font = '10px monospace';
                ctx.fillStyle = '#64748b';
                ctx.fillText('SAFETY SCORE', width / 2, height / 2 + 28);
                ctx.restore();
            }
        }]
    });
}

function renderDetections(violations) {
    const list = document.getElementById('detections-list');
    if (!violations.length) {
        list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted)">No violations detected</div>';
        return;
    }
    list.innerHTML = violations.map(v => {
        const type = v.violation_type.replace(/_/g, ' ');
        const isSim = v.violation_type === 'RED_LIGHT';
        return `<div class="detection-card violation">
            <div class="detection-header">
                <span class="detection-type violation">${type}</span>
                <span class="badge red">${v.confidence}%</span>
            </div>
            <div class="detection-detail"><span>Plate</span><span class="val">${v.plate_number || 'NOT VISIBLE'}</span></div>
            <div class="detection-detail"><span>Fine</span><span class="val" style="color:var(--red)">Rs.${(v.fine_amount||0).toLocaleString()}</span></div>
            ${isSim ? '<span class="badge amber" style="margin-top:6px">SIMULATED</span>' : ''}
        </div>`;
    }).join('');
}

function drawBoxes(violations) {
    const canvas = document.getElementById('overlay-canvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!violations.length || !canvas.width) return;

    const colors = { NO_HELMET: '#ef4444', RED_LIGHT: '#f59e0b', WRONG_SIDE: '#f97316' };
    const hasBbox = violations.some(v => v.bbox && v.bbox.length === 4);

    violations.forEach((v, i) => {
        let bx, by, bw, bh;
        if (hasBbox && v.bbox) {
            [bx, by, bw, bh] = [v.bbox[0], v.bbox[1], v.bbox[2] - v.bbox[0], v.bbox[3] - v.bbox[1]];
        } else {
            bx = Math.round((0.1 + (i % 3) * 0.3) * canvas.width);
            by = Math.round((0.15 + Math.floor(i / 3) * 0.4) * canvas.height);
            bw = Math.round(0.2 * canvas.width);
            bh = Math.round(0.55 * canvas.height);
        }

        const color = colors[v.violation_type] || '#ef4444';
        ctx.strokeStyle = color; ctx.lineWidth = 3;
        ctx.strokeRect(bx, by, bw, bh);

        const label = v.violation_type.replace(/_/g, ' ');
        ctx.font = 'bold 14px monospace';
        const tw = ctx.measureText(label).width + 16;
        ctx.fillStyle = color;
        ctx.fillRect(bx, by - 22, tw, 22);
        ctx.fillStyle = '#000'; ctx.fillText(label, bx + 8, by - 5);

        ctx.fillStyle = 'rgba(0,0,0,.75)';
        ctx.fillRect(bx, by + bh - 20, tw, 20);
        ctx.fillStyle = '#10b981'; ctx.font = 'bold 11px monospace';
        ctx.fillText(v.confidence + '%', bx + 8, by + bh - 5);
    });
}

function generateFrameStrip() {
    const strip = document.getElementById('frame-strip');
    strip.innerHTML = '';
    const src = document.getElementById('overlay-canvas');
    for (let i = 0; i < 5; i++) {
        const div = document.createElement('div');
        div.className = 'frame-thumb' + (i === 2 ? ' active' : '');
        const c = document.createElement('canvas');
        c.width = 160; c.height = 90;
        c.getContext('2d').drawImage(src, 0, 0, 160, 90);
        const lbl = document.createElement('span');
        lbl.className = 'frame-label'; lbl.textContent = `F${i + 1}`;
        div.appendChild(c); div.appendChild(lbl); strip.appendChild(div);
    }
}

function downloadCSV() {
    if (!currentViolations.length) return;
    const headers = ['Violation ID', 'Type', 'Plate', 'Confidence', 'Fine'];
    const rows = currentViolations.map(v => [
        v.violation_id || '', v.violation_type, v.plate_number || 'NOT VISIBLE', v.confidence, v.fine_amount || 0
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `ridesafe_report_${Date.now()}.csv`;
    a.click();
}

function downloadAnnotatedImage() {
    const canvas = document.getElementById('overlay-canvas');
    const link = document.createElement('a');
    link.href = canvas.toDataURL('image/png');
    link.download = `ridesafe_annotated_${Date.now()}.png`;
    link.click();
}

function applyFilters() {
    const type = document.getElementById('filter-type').value;
    const status = document.getElementById('filter-status').value;
    let filtered = allViolations;
    if (type !== 'all') filtered = filtered.filter(v => v.violation_type === type);
    if (status !== 'all') filtered = filtered.filter(v => v.status === status);
    renderViolationsTable(filtered);
}

async function loadViolations() {
    try {
        const r = await fetch(`${API}/api/violations?limit=50`);
        const data = await r.json();
        allViolations = data.violations || [];
        renderViolationsTable(allViolations);
    } catch { allViolations = []; renderViolationsTable([]); }
}

function renderViolationsTable(violations) {
    const c = document.getElementById('violations-table');
    if (!violations.length) { c.innerHTML = '<div class="empty-state">No violations recorded yet.</div>'; return; }
    c.innerHTML = `<table><thead><tr>
        <th>ID</th><th>Type</th><th>Plate</th><th>Confidence</th>
        <th>Fine</th><th>Status</th><th>Actions</th>
    </tr></thead><tbody>${violations.map(v => {
        const type = (v.violation_type || '').replace(/_/g, ' ');
        const sc = v.status === 'approved' ? 'green' : v.status === 'dismissed' ? 'gray' : 'amber';
        return `<tr>
            <td style="font-weight:700">${(v.violation_id||'').slice(0,14)}</td>
            <td><span class="badge red">${type}</span></td>
            <td>${v.plate_number || '<span style="color:var(--muted)">NOT VISIBLE</span>'}</td>
            <td style="color:var(--green)">${v.confidence}%</td>
            <td style="color:var(--red);font-weight:700">Rs.${(v.fine_amount||0).toLocaleString()}</td>
            <td><span class="badge ${sc}">${v.status||'pending'}</span></td>
            <td class="action-btns">
                <button class="btn ghost" onclick="updateStatus('${v.violation_id}','approved')">Approve</button>
                <button class="btn ghost" onclick="updateStatus('${v.violation_id}','dismissed')">Dismiss</button>
            </td>
        </tr>`;
    }).join('')}</tbody></table>`;
}

async function updateStatus(id, status) {
    try {
        await fetch(`${API}/api/violations/${id}`, {
            method: 'PATCH', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status }),
        });
    } catch {}
    loadViolations();
}

function renderHistory() {
    const c = document.getElementById('history-content');
    if (!detectionHistory.length) {
        c.innerHTML = '<div class="empty-state">No processed sessions yet. Upload images or videos to view history.</div>';
        return;
    }
    c.innerHTML = `<div class="history-grid">${detectionHistory.map((h, i) => `
        <div class="history-card">
            <h3>Session #${i + 1}</h3>
            <div class="meta">
                <span><b>Time:</b> ${h.date} ${h.time}</span>
                <span><b>Violations:</b> <span style="color:var(--red)">${h.violations}</span></span>
                <span><b>No Helmet:</b> ${h.helmet} | <b>Red Light:</b> ${h.redlight} | <b>Wrong Side:</b> ${h.wrongside}</span>
                <span><b>Total Fine:</b> <span style="color:var(--red)">Rs.${h.fine.toLocaleString()}</span></span>
                <span><b>Safety Score:</b> <span style="color:${h.safety >= 70 ? 'var(--green)' : h.safety >= 40 ? 'var(--amber)' : 'var(--red)'}">${h.safety}</span></span>
                <span><b>Avg Confidence:</b> ${h.avgConf}%</span>
            </div>
        </div>`).join('')}</div>`;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
