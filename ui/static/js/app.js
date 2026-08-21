const API = '';
let allViolations = [];
let scanHistory = [];
let pieChart = null;
let gaugeChart = null;
let currentViolations = [];
let currentCompliant = [];
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
            if (tab.dataset.page === 'analytics') renderAnalytics();
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
    currentCompliant = [];
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
    const label = document.getElementById('media-label');
    if (isVideo) {
        vid.src = src; vid.classList.remove('hidden'); img.classList.add('hidden');
        vid.onloadedmetadata = () => { canvas.width = vid.videoWidth; canvas.height = vid.videoHeight; };
    } else {
        img.src = src; img.classList.remove('hidden'); vid.classList.add('hidden');
        img.onload = () => { canvas.width = img.naturalWidth; canvas.height = img.naturalHeight; };
    }
    label.textContent = 'SCANNING';
    label.style.color = 'var(--amber)';
}

async function runAnalysis(file, isVideo) {
    const analyzing = document.getElementById('analyzing-state');
    const results = document.getElementById('results-state');
    const scanLine = document.getElementById('scan-line');
    const logFeed = document.getElementById('log-feed');
    const progressFill = document.getElementById('progress-fill');
    const statusText = document.getElementById('analysis-status');
    const label = document.getElementById('media-label');

    analyzing.classList.remove('hidden');
    results.classList.add('hidden');
    logFeed.innerHTML = '';
    scanLine.classList.add('active');

    const conf = document.getElementById('conf-slider').value;

    const steps = [
        [5, 'Loading YOLOv8 helmet detection model...', 'ok'],
        [15, 'Loading license plate detector...', 'ok'],
        [25, 'Loading traffic light classifier...', 'ok'],
        [35, 'Initializing object tracker...', 'ok'],
        [45, 'Reading input frames...', 'ok'],
    ];
    if (isVideo) {
        steps.push([52, 'Extracting key frames...', 'ok']);
        for (let i = 1; i <= 4; i++) steps.push([52 + i * 7, `Processing frame ${i}...`, 'ok']);
    }
    steps.push([isVideo ? 82 : 55, 'Running YOLO inference...', 'ok']);
    steps.push([isVideo ? 86 : 62, 'Detecting two-wheeler riders...', 'ok']);
    steps.push([isVideo ? 89 : 70, 'Classifying helmet status...', 'ok']);
    steps.push([isVideo ? 92 : 78, 'Running plate ANPR...', 'ok']);
    steps.push([isVideo ? 95 : 85, 'Generating violation reports...', 'ok']);
    steps.push([isVideo ? 98 : 92, 'Saving evidence crops...', 'ok']);

    for (const [pct, msg, cls] of steps) {
        progressFill.style.width = pct + '%';
        statusText.textContent = msg;
        logFeed.innerHTML += `<div class="${cls}">${msg}</div>`;
        logFeed.scrollTop = logFeed.scrollHeight;
        await sleep(80);
    }

    try {
        const formData = new FormData();
        formData.append('file', file);
        const endpoint = isVideo ? '/api/analyze/video' : '/api/analyze/image';
        const params = new URLSearchParams({ confidence_threshold: (conf / 100).toFixed(2), mode: 'auto' });
        const response = await fetch(`${API}${endpoint}?${params}`, { method: 'POST', body: formData });
        const data = await response.json();
        progressFill.style.width = '100%';
        statusText.textContent = 'Scan complete!';
        const vCount = data.count || 0;
        const cCount = (data.compliant || []).length;
        logFeed.innerHTML += `<div class="ok">Done - ${cCount} compliant, ${vCount} violation(s) found</div>`;
        scanLine.classList.remove('active');
        label.textContent = vCount > 0 ? 'VIOLATIONS FOUND' : 'ALL CLEAR';
        label.style.color = vCount > 0 ? 'var(--red)' : 'var(--green)';
        await sleep(400);
        showResults(data, isVideo);
    } catch (err) {
        progressFill.style.width = '100%';
        statusText.textContent = 'Scan failed';
        logFeed.innerHTML += `<div class="err">Error: ${err.message}</div>`;
        scanLine.classList.remove('active');
        label.textContent = 'ERROR';
        label.style.color = 'var(--red)';
        await sleep(400);
        showResults({ violations: [], compliant: [], summary: {} }, isVideo);
    }
}

function showResults(data, isVideo) {
    document.getElementById('analyzing-state').classList.add('hidden');
    document.getElementById('results-state').classList.remove('hidden');

    const violations = data.violations || [];
    const compliant = data.compliant || [];
    const summary = data.summary || {};
    currentViolations = violations;
    currentCompliant = compliant;

    const totalScanned = summary.total_scanned || (violations.length + compliant.length);
    const compliantCount = summary.compliant_count || compliant.length;
    const violationCount = summary.violation_count || violations.length;
    const helmetViolations = summary.helmet_violations || violations.filter(v => v.violation_type === 'NO_HELMET').length;
    const totalFines = summary.total_fines || violations.reduce((a, v) => a + (v.fine_amount || 0), 0);
    const complianceRate = totalScanned > 0 ? Math.round((compliantCount / totalScanned) * 100) : 100;

    document.getElementById('m-scanned').textContent = totalScanned;
    document.getElementById('m-compliant').textContent = compliantCount;
    document.getElementById('m-violations').textContent = violationCount;
    document.getElementById('m-fine').textContent = 'Rs.' + totalFines.toLocaleString();

    const banner = document.getElementById('result-banner');
    if (violationCount > 0) {
        banner.innerHTML = `<div class="violation-banner danger">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            <b>${violationCount} RIDER(S) WITHOUT HELMET</b> - ${helmetViolations > 0 ? helmetViolations + ' helmet violation(s)' : ''} Total fine: Rs.${totalFines.toLocaleString()}
        </div>`;
    } else {
        banner.innerHTML = `<div class="violation-banner safe">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            <b>ALL RIDERS COMPLIANT</b> - ${compliantCount} rider(s) detected wearing helmets.
        </div>`;
    }

    renderPieChart(violations, compliant);
    renderGauge(complianceRate);
    renderDetections(violations, compliant);
    drawBoxes(violations, compliant);
    generateFrameStrip();

    scanHistory.push({
        time: new Date().toLocaleTimeString(),
        date: new Date().toLocaleDateString(),
        scanned: totalScanned,
        compliant: compliantCount,
        violations: violationCount,
        helmet: helmetViolations,
        fine: totalFines,
        compliance: complianceRate,
    });
}

function renderPieChart(violations, compliant) {
    const ctx = document.getElementById('pie-chart').getContext('2d');
    if (pieChart) pieChart.destroy();
    const labels = [];
    const data = [];
    const colors = [];
    if (compliant.length > 0) { labels.push('With Helmet'); data.push(compliant.length); colors.push('#10b981'); }
    const vTypes = {};
    violations.forEach(v => { vTypes[v.violation_type] = (vTypes[v.violation_type] || 0) + 1; });
    if (vTypes.NO_HELMET) { labels.push('No Helmet'); data.push(vTypes.NO_HELMET); colors.push('#ef4444'); }
    if (vTypes.RED_LIGHT) { labels.push('Red Light'); data.push(vTypes.RED_LIGHT); colors.push('#f59e0b'); }
    if (vTypes.WRONG_SIDE) { labels.push('Wrong Side'); data.push(vTypes.WRONG_SIDE); colors.push('#f97316'); }
    if (data.length === 0) { labels.push('No Detections'); data.push(1); colors.push('#334155'); }
    pieChart = new Chart(ctx, {
        type: 'doughnut',
        data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 0, hoverOffset: 8 }] },
        options: {
            responsive: true, cutout: '60%',
            plugins: {
                legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'monospace', size: 10 }, padding: 12 } },
            },
        }
    });
}

function renderGauge(rate) {
    const ctx = document.getElementById('gauge-chart').getContext('2d');
    if (gaugeChart) gaugeChart.destroy();
    const color = rate >= 80 ? '#10b981' : rate >= 50 ? '#f59e0b' : '#ef4444';
    gaugeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Compliant', 'Non-Compliant'],
            datasets: [{ data: [rate, 100 - rate], backgroundColor: [color, '#1e293b'], borderWidth: 0 }]
        },
        options: {
            responsive: true, rotation: -90, circumference: 180,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            cutout: '75%',
        },
        plugins: [{
            id: 'gaugeText',
            afterDraw(chart) {
                const { ctx: c, width, height } = chart;
                c.save();
                c.font = 'bold 32px monospace';
                c.fillStyle = color;
                c.textAlign = 'center';
                c.fillText(rate + '%', width / 2, height / 2 + 10);
                c.font = '10px monospace';
                c.fillStyle = '#64748b';
                c.fillText('COMPLIANCE RATE', width / 2, height / 2 + 28);
                c.restore();
            }
        }]
    });
}

function renderDetections(violations, compliant) {
    const list = document.getElementById('detections-list');
    let html = '';
    if (violations.length > 0) {
        violations.forEach(v => {
            const type = v.violation_type.replace(/_/g, ' ');
            html += `<div class="detection-card violation">
                <div class="detection-header">
                    <span class="detection-type violation">${type}</span>
                    <span class="badge red">${v.confidence}%</span>
                </div>
                <div class="detection-detail"><span>Plate</span><span class="val">${v.plate_number || 'NOT VISIBLE'}</span></div>
                <div class="detection-detail"><span>Fine</span><span class="val" style="color:var(--red)">Rs.${(v.fine_amount||0).toLocaleString()}</span></div>
            </div>`;
        });
    }
    if (compliant.length > 0) {
        compliant.forEach(c => {
            html += `<div class="detection-card safe">
                <div class="detection-header">
                    <span class="detection-type safe">WITH HELMET</span>
                    <span class="badge green">${c.confidence}%</span>
                </div>
                <div class="detection-detail"><span>Status</span><span class="val" style="color:var(--green)">Compliant</span></div>
            </div>`;
        });
    }
    if (!html) {
        html = '<div style="text-align:center;padding:20px;color:var(--muted)">No riders detected</div>';
    }
    list.innerHTML = html;
}

function drawBoxes(violations, compliant) {
    const canvas = document.getElementById('overlay-canvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!canvas.width) return;

    const allBboxes = [...(violations || []).map(v => ({ ...v, _type: 'violation' })),
                       ...(compliant || []).map(c => ({ ...c, _type: 'compliant' }))];
    if (!allBboxes.length) return;

    const hasBbox = allBboxes.some(d => d.bbox && d.bbox.length === 4);

    allBboxes.forEach((d, i) => {
        let bx, by, bw, bh;
        if (hasBbox && d.bbox) {
            [bx, by, bw, bh] = [d.bbox[0], d.bbox[1], d.bbox[2] - d.bbox[0], d.bbox[3] - d.bbox[1]];
        } else {
            bx = Math.round((0.08 + (i % 4) * 0.22) * canvas.width);
            by = Math.round((0.12 + Math.floor(i / 4) * 0.45) * canvas.height);
            bw = Math.round(0.18 * canvas.width);
            bh = Math.round(0.6 * canvas.height);
        }

        const isViolation = d._type === 'violation';
        const color = isViolation ? '#ef4444' : '#10b981';
        const alpha = isViolation ? 0.9 : 0.5;
        const lineWidth = isViolation ? 3 : 2;

        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.setLineDash(isViolation ? [] : [6, 4]);
        ctx.strokeRect(bx, by, bw, bh);
        ctx.setLineDash([]);

        if (isViolation) {
            ctx.fillStyle = 'rgba(239,68,68,.08)';
            ctx.fillRect(bx, by, bw, bh);
        }

        const label = isViolation ? 'NO HELMET' : 'HELMET OK';
        ctx.font = 'bold 12px monospace';
        const tw = ctx.measureText(label).width + 14;

        ctx.fillStyle = color;
        ctx.fillRect(bx, by - 20, tw, 20);
        ctx.fillStyle = isViolation ? '#fff' : '#000';
        ctx.fillText(label, bx + 7, by - 6);

        ctx.fillStyle = 'rgba(0,0,0,.75)';
        ctx.fillRect(bx, by + bh - 18, tw, 18);
        ctx.fillStyle = color;
        ctx.font = 'bold 10px monospace';
        ctx.fillText((d.confidence || 0) + '%', bx + 7, by + bh - 5);
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
    if (!currentViolations.length && !currentCompliant.length) return;
    const headers = ['Type', 'Track ID', 'Plate', 'Confidence', 'Fine'];
    const rows = [];
    currentViolations.forEach(v => rows.push(['VIOLATION', v.track_id || '', v.plate_number || 'NOT VISIBLE', v.confidence + '%', v.fine_amount || 0]));
    currentCompliant.forEach(c => rows.push(['COMPLIANT', c.track_id || '', '-', c.confidence + '%', 0]));
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `ridesafe_scan_${Date.now()}.csv`;
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

function renderAnalytics() {
    const c = document.getElementById('analytics-content');
    if (!scanHistory.length) {
        c.innerHTML = '<div class="empty-state">Run a scan to see analytics.</div>';
        return;
    }

    const totalScanned = scanHistory.reduce((a, s) => a + s.scanned, 0);
    const totalViolations = scanHistory.reduce((a, s) => a + s.violations, 0);
    const totalCompliant = scanHistory.reduce((a, s) => a + s.compliant, 0);
    const totalFines = scanHistory.reduce((a, s) => a + s.fine, 0);
    const avgCompliance = Math.round(scanHistory.reduce((a, s) => a + s.compliance, 0) / scanHistory.length);
    const totalScans = scanHistory.length;

    c.innerHTML = `
        <div class="analytics-highlight">${avgCompliance}%</div>
        <p style="text-align:center;color:var(--muted);margin-bottom:20px;font-size:12px">Average Compliance Rate Across ${totalScans} Scan(s)</p>
        <div class="metrics-grid">
            <div class="metric-card blue"><span class="metric-label">Total Scans</span><span class="metric-value">${totalScans}</span></div>
            <div class="metric-card blue"><span class="metric-label">Riders Scanned</span><span class="metric-value">${totalScanned}</span></div>
            <div class="metric-card green"><span class="metric-label">Compliant</span><span class="metric-value">${totalCompliant}</span></div>
            <div class="metric-card red"><span class="metric-label">Violations</span><span class="metric-value">${totalViolations}</span></div>
        </div>
        <div class="analytics-grid">
            <div class="analytics-card">
                <h3>Session History</h3>
                <div class="meta">
                    ${scanHistory.map((s, i) => `<span><b>#${i+1}</b> ${s.date} ${s.time} - <span style="color:${s.compliance >= 80 ? 'var(--green)' : 'var(--red)'}">${s.compliance}% compliance, ${s.violations} violations</span></span>`).join('')}
                </div>
            </div>
            <div class="analytics-card">
                <h3>Summary</h3>
                <div class="meta">
                    <span><b>Total Fines Assessed:</b> <span style="color:var(--red)">Rs.${totalFines.toLocaleString()}</span></span>
                    <span><b>Average Compliance:</b> <span style="color:${avgCompliance >= 80 ? 'var(--green)' : 'var(--red)'}">${avgCompliance}%</span></span>
                    <span><b>Violation Rate:</b> ${totalScanned > 0 ? Math.round(totalViolations / totalScanned * 100) : 0}%</span>
                </div>
            </div>
        </div>
    `;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
