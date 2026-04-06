/* ── State ── */
let selectedFile = null;
let currentResult = null;

/* ── DOM refs ── */
const dropZone    = document.getElementById('dropZone');
const fileInput   = document.getElementById('fileInput');
const fileInfo    = document.getElementById('fileInfo');
const fileName    = document.getElementById('fileName');
const clearFile   = document.getElementById('clearFile');
const jdInput     = document.getElementById('jdInput');
const analyzeBtn  = document.getElementById('analyzeBtn');
const actionHint  = document.getElementById('actionHint');
const results        = document.getElementById('results');
const exportDocxBtn  = document.getElementById('exportDocxBtn');
const exportPdfBtn   = document.getElementById('exportPdfBtn');

/* ── File handling ── */
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) setFile(fileInput.files[0]);
});

clearFile.addEventListener('click', () => {
  selectedFile = null;
  fileInput.value = '';
  fileInfo.hidden = true;
  dropZone.hidden = false;
  dropZone.classList.remove('has-file');
  updateAnalyzeBtn();
});

function setFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'docx'].includes(ext)) {
    showToast('Only PDF and DOCX files are supported');
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast('File too large — max 5 MB');
    return;
  }
  selectedFile = file;
  fileName.textContent = file.name;
  fileInfo.hidden = false;
  dropZone.classList.add('has-file');
  updateAnalyzeBtn();
}

/* ── JD input ── */
jdInput.addEventListener('input', updateAnalyzeBtn);

function updateAnalyzeBtn() {
  const ready = selectedFile && jdInput.value.trim().length > 20;
  analyzeBtn.disabled = !ready;
  actionHint.textContent = ready
    ? 'Ready — click to analyze and optimize your resume'
    : 'Upload a resume and paste a job description to begin';
}

/* ── Analyze ── */
analyzeBtn.addEventListener('click', async () => {
  if (!selectedFile || !jdInput.value.trim()) return;

  setBtnLoading(true);
  results.hidden = true;

  const formData = new FormData();
  formData.append('resume', selectedFile);
  formData.append('job_description', jdInput.value.trim());

  try {
    const res = await fetch('/api/optimize', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.detail || 'Server error — check the backend logs');
      return;
    }

    currentResult = data;
    renderResults(data);
  } catch (err) {
    showToast('Network error — is the server running?');
  } finally {
    setBtnLoading(false);
  }
});

function setBtnLoading(loading) {
  const text    = analyzeBtn.querySelector('.btn-text');
  const spinner = analyzeBtn.querySelector('.spinner');
  analyzeBtn.disabled = loading;
  text.textContent    = loading ? 'Optimizing…' : 'Analyze & Optimize';
  spinner.hidden      = !loading;
}

/* ── Render Results ── */
function renderResults(data) {
  // Score
  const score = data.match_score;
  document.getElementById('scoreValue').textContent = score;
  const fill  = document.getElementById('progressFill');
  const circle = document.getElementById('scoreCircle');
  fill.style.width = score + '%';
  if (score >= 70) {
    fill.style.background = 'var(--green)';
    circle.className = 'score-circle good';
  } else if (score >= 45) {
    fill.style.background = 'var(--yellow)';
    circle.className = 'score-circle ok';
  } else {
    fill.style.background = 'var(--red)';
    circle.className = 'score-circle bad';
  }

  // Keywords
  renderChips('missingKeywords', data.missing_keywords, 'missing');
  renderChips('presentKeywords', data.present_keywords, 'present');

  // ATS issues
  const issuesCard = document.getElementById('atsIssuesCard');
  const issuesList = document.getElementById('atsIssues');
  if (data.ats_issues && data.ats_issues.length) {
    issuesList.innerHTML = data.ats_issues.map(i => `<li>${escHtml(i)}</li>`).join('');
    issuesCard.hidden = false;
  } else {
    issuesCard.hidden = true;
  }

  // Changes
  const changesCard = document.getElementById('changesCard');
  const changesList = document.getElementById('changesList');
  const validChanges = (data.changes_made || []).filter(c => !c.startsWith('Error:'));
  if (validChanges.length) {
    changesList.innerHTML = validChanges.map(c => `<li>${escHtml(c)}</li>`).join('');
    changesCard.hidden = false;
  } else {
    changesCard.hidden = true;
  }

  // Diff
  document.getElementById('originalText').innerHTML  = renderDiff(data.original_text,  data.optimized_text, 'original');
  document.getElementById('optimizedText').innerHTML = renderDiff(data.original_text, data.optimized_text, 'optimized');

  results.hidden = false;
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderChips(containerId, keywords, type) {
  const el = document.getElementById(containerId);
  if (!keywords || !keywords.length) {
    el.innerHTML = `<span style="color:var(--text-muted);font-size:12px">None found</span>`;
    return;
  }
  el.innerHTML = keywords
    .map(kw => `<span class="chip ${type}">${escHtml(kw)}</span>`)
    .join('');
}

/* Simple line-level diff: highlight lines in optimized that differ from original */
function renderDiff(originalText, optimizedText, side) {
  if (!originalText && !optimizedText) return '';

  const origLines = (originalText || '').split('\n');
  const optLines  = (optimizedText || '').split('\n');
  const origSet   = new Set(origLines.map(l => l.trim()));
  const optSet    = new Set(optLines.map(l => l.trim()));

  if (side === 'original') {
    return origLines.map(line => escHtml(line)).join('\n');
  } else {
    return optLines.map(line => {
      const trimmed = line.trim();
      if (trimmed && !origSet.has(trimmed)) {
        return `<span class="diff-add">${escHtml(line)}</span>`;
      }
      return escHtml(line);
    }).join('\n');
  }
}

/* ── Export helpers ── */
async function doExport(endpoint, filename, btn, label) {
  if (!currentResult || !currentResult.optimized_text) {
    showToast('No optimized resume to export');
    return;
  }
  btn.textContent = 'Exporting…';
  btn.disabled    = true;
  try {
    const formData = new FormData();
    formData.append('optimized_text', currentResult.optimized_text);
    const res = await fetch(endpoint, { method: 'POST', body: formData });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Export failed' }));
      showToast(err.detail || 'Export failed');
      return;
    }
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    showToast('Export failed — check backend logs');
  } finally {
    btn.textContent = label;
    btn.disabled    = false;
  }
}

exportDocxBtn.addEventListener('click', () =>
  doExport('/api/export/docx', 'optimized_resume.docx', exportDocxBtn, '⬇ Export as Word (.docx)')
);

exportPdfBtn.addEventListener('click', () =>
  doExport('/api/export', 'optimized_resume.pdf', exportPdfBtn, 'Export as PDF')
);

/* ── Toast ── */
function showToast(msg) {
  const toast = document.getElementById('toast');
  document.getElementById('toastMsg').textContent = msg;
  toast.hidden = false;
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(hideToast, 5000);
}

function hideToast() {
  document.getElementById('toast').hidden = true;
}

/* ── Utils ── */
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
