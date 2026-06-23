/* ═══════════════════════════════════════════════════════════════
   AgriAI Disease Recognition JavaScript
   • Image analysis with ML model
   • CSV dataset upload
   • Model training with real-time log polling
═══════════════════════════════════════════════════════════════ */

// ── Utility ──────────────────────────────────────────────
function getCsrf() {
  const c = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return c ? c.split('=')[1] : '';
}
function showMsg(id, type, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `msg-box ${type}`;
  el.textContent = text;
}

// ── Tab Switching ─────────────────────────────────────────
function switchDTab(tab, btn) {
  document.querySelectorAll('.dtab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.dtab-content').forEach(c => c.style.display = 'none');
  if (btn) btn.classList.add('active');
  const el = document.getElementById('tab-' + tab);
  if (el) el.style.display = 'block';
}

// ═══════════════════════════════════════════
// IMAGE ANALYSIS
// ═══════════════════════════════════════════

function previewImage(input) {
  const file = input.files[0];
  if (!file) return;
  const preview = document.getElementById('imagePreview');
  const anim    = document.getElementById('uploadAnim');
  const reader  = new FileReader();
  reader.onload = e => {
    preview.src           = e.target.result;
    preview.style.display = 'block';
    anim.style.display    = 'none';
  };
  reader.readAsDataURL(file);
}

// Drag and drop
const uploadZone = document.getElementById('uploadZone');
if (uploadZone) {
  ['dragover','dragenter'].forEach(evt => {
    uploadZone.addEventListener(evt, e => {
      e.preventDefault();
      uploadZone.classList.add('drag-over');
    });
  });
  ['dragleave','drop'].forEach(evt => {
    uploadZone.addEventListener(evt, e => {
      uploadZone.classList.remove('drag-over');
    });
  });
  uploadZone.addEventListener('drop', e => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      const input = document.getElementById('diseaseImage');
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      previewImage(input);
    }
  });
}

async function analyzeDisease() {
  const imageInput = document.getElementById('diseaseImage');
  const cropName   = document.getElementById('cropNameSelect').value;

  if (!imageInput.files[0])
    return showMsg('analyzeMsg', 'error', '⚠️ Please upload a crop image first');

  // Show loading
  document.getElementById('resultPlaceholder').style.display = 'none';
  document.getElementById('resultContent').style.display     = 'none';
  document.getElementById('analyzeLoading').style.display    = 'flex';

  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Analyzing...';

  // Animate scan labels
  const labels = [
    'Extracting color features...',
    'Analyzing leaf texture...',
    'Running disease classifier...',
    'Generating treatment plan...'
  ];
  let li = 0;
  const labelInterval = setInterval(() => {
    const el = document.getElementById('scanLabel');
    if (el) el.textContent = labels[li++ % labels.length];
  }, 900);

  const formData = new FormData();
  formData.append('image', imageInput.files[0]);
  formData.append('crop_name', cropName);

  try {
    const res  = await fetch('/api/disease/analyze/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf() },
      body: formData
    });
    const data = await res.json();
    clearInterval(labelInterval);
    document.getElementById('analyzeLoading').style.display = 'none';

    if (data.success) {
      displayResult(data);
    } else {
      document.getElementById('resultPlaceholder').style.display = 'block';
      showMsg('analyzeMsg', 'error', '❌ ' + (data.error || 'Analysis failed'));
    }
  } catch (e) {
    clearInterval(labelInterval);
    document.getElementById('analyzeLoading').style.display = 'none';
    document.getElementById('resultPlaceholder').style.display = 'block';
    showMsg('analyzeMsg', 'error', '❌ Network error. Please try again.');
  }

  btn.disabled = false;
  btn.innerHTML = '<i class="fa fa-search"></i> Analyze Disease';
}

function displayResult(data) {
  const content = document.getElementById('resultContent');
  content.style.display = 'block';

  document.getElementById('diseaseName').textContent = data.disease;
  document.getElementById('treatmentText').textContent = data.treatment;

  // Model tag
  const tag = document.getElementById('modelTag');
  tag.textContent = data.model_used === 'ml_trained' ? '🧠 ML Model' : '⚡ Rule-Based';
  tag.className   = 'model-tag ' + (data.model_used === 'ml_trained' ? 'ml' : 'rule');

  // Severity
  const sp   = document.getElementById('severityPill');
  sp.textContent = data.severity || '—';
  const sevColors = { None:'#d1fae5 #065f46', Low:'#d1fae5 #065f46', Medium:'#fef3c7 #92400e', High:'#fee2e2 #991b1b', Critical:'#fecaca #7f1d1d', Unknown:'#f3f4f6 #374151' };
  const [bg, col] = (sevColors[data.severity] || sevColors.Unknown).split(' ');
  sp.style.background = bg;
  sp.style.color = col;

  // Disease icon
  const icons = { Healthy:'✅', Rust:'🟤', Blight:'🟡', Mildew:'⚪', Blast:'⚫', Virus:'🔴', Wilt:'🟠', Rot:'🟫' };
  const matchedIcon = Object.entries(icons).find(([k]) => data.disease.includes(k));
  document.getElementById('diseaseIconLg').textContent = matchedIcon ? matchedIcon[1] : '🦠';

  // Confidence bar animation
  setTimeout(() => {
    document.getElementById('confFill').style.width = `${data.confidence}%`;
    document.getElementById('confPct').textContent  = `${data.confidence}%`;
    // Color based on confidence
    const color = data.confidence >= 85 ? '#22c55e' : data.confidence >= 65 ? '#f59e0b' : '#ef4444';
    document.getElementById('confFill').style.background = `linear-gradient(90deg, ${color}, ${color}cc)`;
  }, 100);

  // Top 3 predictions
  if (data.all_predictions && data.all_predictions.length > 1) {
    const top3Section = document.getElementById('top3Section');
    const top3List    = document.getElementById('top3List');
    top3Section.style.display = 'block';
    top3List.innerHTML = data.all_predictions.slice(0, 3).map((p, i) => `
      <div class="pred-item ${i === 0 ? 'top' : ''}">
        <span class="pred-rank">#${i+1}</span>
        <span class="pred-name">${p.disease}</span>
        <div class="pred-bar-wrap">
          <div class="pred-bar" style="width:${p.confidence}%;background:${i===0?'var(--green-light)':'#94a3b8'}"></div>
        </div>
        <span class="pred-conf">${p.confidence}%</span>
      </div>
    `).join('');
  }

  // Animate in
  content.style.animation = 'none';
  content.offsetHeight;
  content.style.animation = 'slideUp 0.5s ease both';
}


// ═══════════════════════════════════════
// CSV DATASET UPLOAD
// ═══════════════════════════════════════

// CSV drag and drop
const csvZone = document.getElementById('csvDropZone');
if (csvZone) {
  ['dragover','dragenter'].forEach(evt => {
    csvZone.addEventListener(evt, e => { e.preventDefault(); csvZone.classList.add('drag-over'); });
  });
  ['dragleave','drop'].forEach(evt => {
    csvZone.addEventListener(evt, () => csvZone.classList.remove('drag-over'));
  });
  csvZone.addEventListener('drop', e => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.csv')) {
      const input = document.getElementById('csvFileInput');
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      handleCsvSelect(input);
    } else {
      alert('Please drop a .csv file');
    }
  });
}

function handleCsvSelect(input) {
  const file = input.files[0];
  if (!file) return;
  const textEl = document.getElementById('csvDropText');
  if (textEl) {
    textEl.textContent = `✅ Selected: ${file.name} (${(file.size/1024/1024).toFixed(2)} MB)`;
    textEl.style.color = 'var(--green-mid)';
  }
  // Auto-fill name
  const nameEl = document.getElementById('datasetName');
  if (nameEl && !nameEl.value) {
    nameEl.value = file.name.replace('.csv', '').replace(/_/g, ' ');
  }
}

async function uploadDataset() {
  const csvInput = document.getElementById('csvFileInput');
  const name     = document.getElementById('datasetName').value.trim();
  const desc     = document.getElementById('datasetDesc').value.trim();

  if (!csvInput.files[0])  return showMsg('uploadMsg', 'error', '⚠️ Please select a CSV file first');
  if (!name)               return showMsg('uploadMsg', 'error', '⚠️ Please enter a dataset name');

  const btn = document.getElementById('uploadDatasetBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Uploading...';

  const formData = new FormData();
  formData.append('csv_file',   csvInput.files[0]);
  formData.append('name',       name);
  formData.append('description',desc);

  try {
    const res  = await fetch('/api/disease/upload-dataset/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf() },
      body: formData
    });
    const data = await res.json();

    if (data.success) {
      showMsg('uploadMsg', 'success', `✅ ${data.message}`);
      showDatasetPreview(data);
      // Refresh page to show in list
      setTimeout(() => location.reload(), 2000);
    } else {
      showMsg('uploadMsg', 'error', '❌ ' + (data.error || 'Upload failed'));
    }
  } catch (e) {
    showMsg('uploadMsg', 'error', '❌ Network error. Please try again.');
  }

  btn.disabled = false;
  btn.innerHTML = '<i class="fa fa-upload"></i> Upload Dataset';
}

function showDatasetPreview(data) {
  const preview = document.getElementById('datasetPreview');
  const stats   = document.getElementById('datasetStats');
  preview.style.display = 'block';
  stats.innerHTML = `
    <div class="ds-stat-grid">
      <div class="ds-stat"><strong>${data.total_rows}</strong><small>Total Rows</small></div>
      <div class="ds-stat"><strong>${data.unique_labels}</strong><small>Disease Classes</small></div>
    </div>
    <div class="ds-label-list">
      ${(data.label_names || []).map(l => `<span class="lbl-chip">${l}</span>`).join('')}
    </div>
  `;
}


// ═══════════════════════════════════════
// MODEL TRAINING
// ═══════════════════════════════════════

let trainingPollInterval = null;

async function trainModel(datasetId, btn) {
  if (!confirm('Start training ML model with this dataset? This may take a few minutes.')) return;

  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Starting...';

  const logSection  = document.getElementById('trainingLogSection');
  const logEl       = document.getElementById('trainingLog');
  const progressFill= document.getElementById('trainProgressFill');
  const progressLabel = document.getElementById('trainProgressLabel');

  logSection.style.display = 'block';
  logEl.textContent = '🚀 Training started...\n';

  try {
    const res  = await fetch('/api/disease/train/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({ dataset_id: datasetId })
    });
    const data = await res.json();

    if (!data.success) {
      logEl.textContent = '❌ ' + (data.error || 'Failed to start training');
      btn.disabled = false;
      btn.innerHTML = '<i class="fa fa-brain"></i> Train';
      return;
    }

    logEl.textContent += 'Training in progress. Polling for updates...\n';

    // Poll for status every 3 seconds
    let progress = 0;
    trainingPollInterval = setInterval(async () => {
      try {
        const statusRes  = await fetch('/api/disease/model-status/');
        const statusData = await statusRes.json();

        if (statusData.training_log) {
          logEl.textContent = statusData.training_log;
          logEl.scrollTop   = logEl.scrollHeight;
        }

        // Simulate progress
        progress = Math.min(progress + Math.random() * 15, 90);
        progressFill.style.width  = progress + '%';
        progressLabel.textContent = Math.round(progress) + '%';

        // Update dataset status in list
        const dsEl = document.getElementById(`ds-${datasetId}`);
        if (dsEl) {
          const statusBadge = dsEl.querySelector('.ds-status');
          if (statusBadge) statusBadge.textContent = statusData.status || 'training';
        }

        if (statusData.status === 'trained') {
          clearInterval(trainingPollInterval);
          progressFill.style.width  = '100%';
          progressLabel.textContent = '100%';
          progressFill.style.background = 'var(--green-light)';
          logEl.textContent += `\n\n✅ TRAINING COMPLETE!\nAccuracy: ${statusData.accuracy}%\nModel saved and ready to use!`;
          logEl.scrollTop = logEl.scrollHeight;

          // Refresh status box
          document.getElementById('modelStatusBox').innerHTML = `
            <div class="status-indicator trained">
              <span class="status-dot"></span>
              <div>
                <strong>✅ Trained Model Active (${statusData.accuracy}% accuracy)</strong>
                <small>Classes: ${(statusData.label_names || []).join(', ')}</small>
              </div>
            </div>`;

          btn.disabled = false;
          btn.innerHTML = '<i class="fa fa-check"></i> Trained!';
          btn.style.color = 'var(--green-mid)';

        } else if (statusData.status === 'failed') {
          clearInterval(trainingPollInterval);
          logEl.textContent += '\n\n❌ Training failed. Check log above for details.';
          progressFill.style.background = '#ef4444';
          btn.disabled = false;
          btn.innerHTML = '<i class="fa fa-redo"></i> Retry';
        }

      } catch (e) {
        // Poll error — keep trying
      }
    }, 3000);

  } catch (e) {
    logEl.textContent = '❌ Network error: ' + e.message;
    btn.disabled = false;
    btn.innerHTML = '<i class="fa fa-brain"></i> Train';
  }
}

// ── Cleanup on page unload ────────────────────────────────
window.addEventListener('beforeunload', () => {
  if (trainingPollInterval) clearInterval(trainingPollInterval);
});
