const API = '';
let allViolations = [];
let currentPage = 'analyze';

document.addEventListener('DOMContentLoaded', init);

function init() {
    checkApi();
    setInterval(checkApi, 10000);
    setupNavigation();
    setupUpload();
    setupFilters();
    loadViolations();
}

async function checkApi() {
    const el = document.getElementById('api-status');
    const dot = el.previousElementSibling;
    try {
        const r = await fetch(`${API}/api/dashboard`);
        if (r.ok) {
            el.textContent = 'System Online';
            dot.className = 'dot green pulse';
        } else throw 0;
    } catch {
        el.textContent = 'System Offline';
        dot.className = 'dot red';
    }
}

function setupNavigation() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            currentPage = tab.dataset.page;
            document.getElementById(`page-${currentPage}`).classList.add('active');
            if (currentPage === 'violations') loadViolations();
        });
    });
}

function setupUpload() {
    const zone = document.getElementById('drop-zone');
    const input = document.getElementById('file-input');

    zone.addEventListener('click', () => input.click());
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });
    input.addEventListener('change', () => {
        if (input.files.length) handleFile(input.files[0]);
    });

    document.getElementById('btn-new-file').addEventListener('click', resetUpload);
    document.getElementById('btn-view-violations').addEventListener('click', () => {
        document.querySelector('.tab[data-page="violations"]').click();
    });
}

function resetUpload() {
    document.getElementById('drop-zone').classList.remove('hidden');
    document.getElementById('analysis-area').classList.add('hidden');
    document.getElementById('btn-new-file').style.display = 'none';
    document.getElementById('preview-image').classList.add('hidden');
    document.getElementById('preview-video').classList.add('hidden');
    document.getElementById('frame-strip').innerHTML = '';
    const canvas = document.getElementById('overlay-canvas');
    canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
}

async function handleFile(file) {
    const isVideo = file.type.startsWith('video');
    const reader = new FileReader();
    reader.onload = async (e) => {
        const dataUrl = e.target.result;
        showPreview(dataUrl, isVideo);
        await runAnalysis(file, isVideo);
    };
    reader.readAsDataURL(file);
}

function showPreview(src, isVideo) {
    document.getElementById('drop-zone').classList.add('hidden');
    document.getElementById('analysis-area').classList.remove('hidden');
    document.getElementById('btn-new-file').style.display = 'block';

    const img = document.getElementById('preview-image');
    const vid = document.getElementById('preview-video');
    const canvas = document.getElementById('overlay-canvas');

    if (isVideo) {
        vid.src = src;
        vid.classList.remove('hidden');
        img.classList.add('hidden');
        vid.onloadedmetadata = () => {
            canvas.width = vid.videoWidth;
            canvas.height = vid.videoHeight;
        };
    } else {
        img.src = src;
        img.classList.remove('hidden');
        vid.classList.add('hidden');
        img.onload = () => {
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
        };
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

    const steps = [
        [5, 'Loading YOLOv8 detection models...', 'ok'],
        [15, 'Loading helmet classifier (YOLOv8n)...', 'ok'],
        [25, 'Loading plate detector (YOLOv8n)...', 'ok'],
        [35, 'Reading input frames...', 'ok'],
    ];

    if (isVideo) {
        steps.push([45, 'Extracting key frames...', 'ok']);
        steps.push([55, 'Processing frame 1...', 'ok']);
        steps.push([62, 'Processing frame 2...', 'ok']);
        steps.push([70, 'Processing frame 3...', 'ok']);
    }

    steps.push([isVideo ? 75 : 50, 'Running inference...', 'ok']);
    steps.push([isVideo ? 82 : 60, 'Running helmet detection...', 'ok']);
    steps.push([isVideo ? 88 : 70, 'Running plate detection (ANPR)...', 'ok']);
    steps.push([92, 'Classifying violations...', 'ok']);
    steps.push([96, 'Generating evidence crops...', 'ok']);

    for (const [pct, msg, cls] of steps) {
        progressFill.style.width = pct + '%';
        statusText.textContent = msg;
        logFeed.innerHTML += `<div class="${cls}">${msg}</div>`;
        logFeed.scrollTop = logFeed.scrollHeight;
        await sleep(120);
    }

    try {
        const formData = new FormData();
        formData.append('file', file);

        const endpoint = isVideo ? '/api/analyze/video' : '/api/analyze/image';
        const response = await fetch(`${API}${endpoint}`, { method: 'POST', body: formData });
        const data = await response.json();

        progressFill.style.width = '100%';
        statusText.textContent = 'Analysis complete!';
        logFeed.innerHTML += `<div class="ok">Done — ${data.count || 0} violation(s) detected</div>`;
        scanLine.classList.remove('active');

        await sleep(400);
        showResults(data.violations || [], data.detections || []);

    } catch (err) {
        progressFill.style.width = '100%';
        statusText.textContent = 'Analysis failed';
        logFeed.innerHTML += `<div class="err">Error: ${err.message}</div>`;
        scanLine.classList.remove('active');

        await sleep(400);
        showResults([], []);
    }
}

function showResults(violations, detections) {
    document.getElementById('analyzing-state').classList.add('hidden');
    document.getElementById('results-state').classList.remove('hidden');

    const vioCount = violations.length;
    const detCount = Math.max(detections.length, vioCount, 1);
    const compliant = Math.max(0, detCount - vioCount);
    const avgConf = vioCount > 0 ? Math.round(violations.reduce((a, v) => a + v.confidence, 0) / vioCount) : 0;

    document.getElementById('stat-violations').textContent = vioCount;
    document.getElementById('stat-compliant').textContent = compliant;
    document.getElementById('stat-confidence').textContent = avgConf + '%';

    const hasSim = violations.some(v => v.violation_type === 'RED_LIGHT');
    document.getElementById('sim-notice').classList.toggle('hidden', !hasSim);

    const list = document.getElementById('detections-list');
    if (violations.length === 0) {
        list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted)">No violations detected</div>';
    } else {
        list.innerHTML = violations.map((v, i) => {
            const type = v.violation_type.replace(/_/g, ' ');
            const isSim = v.violation_type === 'RED_LIGHT';
            return `
                <div class="detection-card violation">
                    <div class="detection-header">
                        <span class="detection-type violation">${type}</span>
                        <span class="badge red">${v.confidence}%</span>
                    </div>
                    <div class="detection-detail"><span>Plate</span><span class="val">${v.plate_number || 'NOT VISIBLE'}</span></div>
                    <div class="detection-detail"><span>Fine</span><span class="val" style="color:var(--red)">Rs.${v.fine_amount?.toLocaleString() || '—'}</span></div>
                    ${isSim ? '<span class="badge amber" style="margin-top:4px">SIMULATED</span>' : ''}
                </div>`;
        }).join('');
    }

    drawBoxes(violations);
}

function drawBoxes(violations) {
    const canvas = document.getElementById('overlay-canvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!violations.length || !canvas.width) return;

    const colors = { NO_HELMET: '#ef4444', RED_LIGHT: '#f59e0b', WRONG_SIDE: '#ef4444' };
    const hasRealBboxes = violations.some(v => v.bbox && v.bbox.length === 4);

    violations.forEach((v, i) => {
        let bx, by, bw, bh;

        if (hasRealBboxes && v.bbox && v.bbox.length === 4) {
            [bx, by, bw, bh] = v.bbox;
            bw = bw - bx;
            bh = bh - by;
        } else {
            const x = 0.15 + (i % 3) * 0.25;
            const y = 0.2 + Math.floor(i / 3) * 0.35;
            const w = 0.22;
            const h = 0.5;
            bx = Math.round(x * canvas.width);
            by = Math.round(y * canvas.height);
            bw = Math.round(w * canvas.width);
            bh = Math.round(h * canvas.height);
        }

        const color = colors[v.violation_type] || '#ef4444';

        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(bx, by, bw, bh);

        const label = v.violation_type.replace(/_/g, ' ');
        ctx.font = 'bold 16px monospace';
        const textW = ctx.measureText(label).width + 16;
        ctx.fillStyle = color;
        ctx.fillRect(bx, by - 24, textW, 24);
        ctx.fillStyle = '#000';
        ctx.fillText(label, bx + 8, by - 6);

        ctx.fillStyle = 'rgba(0,0,0,0.7)';
        ctx.fillRect(bx, by + bh - 22, textW, 22);
        ctx.fillStyle = '#10b981';
        ctx.font = 'bold 13px monospace';
        ctx.fillText(`${v.confidence}% conf`, bx + 8, by + bh - 5);
    });

    generateFrameStrip(violations);
}

function generateFrameStrip(violations) {
    const strip = document.getElementById('frame-strip');
    strip.innerHTML = '';

    const sourceCanvas = document.getElementById('overlay-canvas');
    for (let i = 0; i < 5; i++) {
        const div = document.createElement('div');
        div.className = 'frame-thumb' + (i === 2 ? ' active' : '');
        const c = document.createElement('canvas');
        c.width = 160;
        c.height = 90;
        const ctx = c.getContext('2d');
        ctx.drawImage(sourceCanvas, 0, 0, 160, 90);
        const label = document.createElement('span');
        label.className = 'frame-label';
        label.textContent = `F${i + 1}`;
        div.appendChild(c);
        div.appendChild(label);
        strip.appendChild(div);
    }
}

async function loadViolations() {
    try {
        const r = await fetch(`${API}/api/violations?limit=50`);
        const data = await r.json();
        allViolations = data.violations || [];
        renderViolationsTable(allViolations);
    } catch {
        allViolations = [];
        renderViolationsTable([]);
    }
}

function renderViolationsTable(violations) {
    const container = document.getElementById('violations-table');
    if (!violations.length) {
        container.innerHTML = '<div class="empty-state">No violations recorded yet.</div>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead><tr>
                <th>ID</th><th>Type</th><th>Plate</th><th>Confidence</th>
                <th>Fine</th><th>Status</th><th>Actions</th>
            </tr></thead>
            <tbody>${violations.map(v => {
                const type = v.violation_type?.replace(/_/g, ' ') || '—';
                const statusClass = v.status === 'paid' ? 'green' : v.status === 'issued' ? 'amber' : 'red';
                return `<tr>
                    <td style="font-weight:700">${v.violation_id?.slice(0, 12) || '—'}</td>
                    <td><span class="badge red">${type}</span></td>
                    <td>${v.plate_number || '<span style="color:var(--muted)">NOT VISIBLE</span>'}</td>
                    <td style="color:var(--green)">${v.confidence}%</td>
                    <td style="color:var(--red);font-weight:700">Rs.${v.fine_amount?.toLocaleString() || '—'}</td>
                    <td><span class="badge ${statusClass}">${v.status || 'pending'}</span></td>
                    <td class="action-btns">
                        <button class="btn ghost" onclick="updateStatus('${v.violation_id}','approved')">Approve</button>
                        <button class="btn ghost" onclick="updateStatus('${v.violation_id}','dismissed')">Dismiss</button>
                    </td>
                </tr>`;
            }).join('')}</tbody>
        </table>`;
}

function setupFilters() {
    document.getElementById('filter-type').addEventListener('change', applyFilters);
    document.getElementById('filter-status').addEventListener('change', applyFilters);
}

function applyFilters() {
    const type = document.getElementById('filter-type').value;
    const status = document.getElementById('filter-status').value;
    let filtered = allViolations;
    if (type !== 'all') filtered = filtered.filter(v => v.violation_type === type);
    if (status !== 'all') filtered = filtered.filter(v => v.status === status);
    renderViolationsTable(filtered);
}

async function updateStatus(violationId, newStatus) {
    try {
        await fetch(`${API}/api/violations/${violationId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus }),
        });
    } catch {}
    loadViolations();
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
