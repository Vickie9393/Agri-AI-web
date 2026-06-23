/* AgriAI — Pest Control JS */
function getCsrf(){const c=document.cookie.split(';').find(c=>c.trim().startsWith('csrftoken='));return c?c.split('=')[1]:'';}
function showMsg(id,type,text){const el=document.getElementById(id);if(!el)return;el.className=`msg-box ${type}`;el.textContent=text;}

function quickFill(pestName) {
  openModal('addPestModal');
  setTimeout(() => {
    const el = document.getElementById('pestName');
    if (el) el.value = pestName;
  }, 80);
}

async function submitPestReport() {
  const crop     = document.getElementById('pestCrop')?.value.trim();
  const pest     = document.getElementById('pestName')?.value.trim();
  const severity = document.getElementById('pestSeverity')?.value;
  const area     = document.getElementById('pestArea')?.value;
  const symptoms = document.getElementById('pestSymptoms')?.value.trim();

  if (!crop||!pest||!symptoms)
    return showMsg('pestMsg','error','⚠️ Fill crop name, pest name, and symptoms');

  const btn = document.querySelector('#addPestModal .btn-primary');
  if (btn) { btn.disabled=true; btn.innerHTML='<i class="fa fa-spinner fa-spin"></i> Analysing...'; }

  try {
    const res  = await fetch('/api/pest/add/', {
      method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':getCsrf()},
      body: JSON.stringify({ crop_name:crop, pest_name:pest, severity, affected_area:parseFloat(area)||1, symptoms })
    });
    const data = await res.json();
    if (data.success) {
      showMsg('pestMsg','success','✅ Record saved!');
      showPestResult(data);
      if(btn){btn.disabled=false;btn.innerHTML='Get AI Recommendation 🤖';}
      setTimeout(()=>{ closeModal('addPestModal'); location.reload(); }, 3500);
    } else {
      showMsg('pestMsg','error','❌ '+(data.error||'Failed'));
      if(btn){btn.disabled=false;btn.innerHTML='Get AI Recommendation 🤖';}
    }
  } catch {
    showMsg('pestMsg','error','❌ Network error');
    if(btn){btn.disabled=false;btn.innerHTML='Get AI Recommendation 🤖';}
  }
}

function showPestResult(data) {
  const box = document.getElementById('pestResult');
  if (!box) return;
  box.style.display = 'block';
  box.innerHTML = `
    <h4 style="margin-bottom:.75rem;color:var(--green-deep)">🤖 AI Recommendation</h4>
    <p><strong>💊 Pesticide:</strong> ${data.pesticide}</p>
    <p><strong>📏 Dosage:</strong> ${data.dosage}</p>
    <p><strong>🌱 Method:</strong> ${data.method}</p>
    <p style="color:var(--green-mid)"><strong>🌿 Organic:</strong> ${data.organic}</p>
    <p style="margin-top:.5rem;font-size:.83rem;color:#555">${data.recommendation}</p>
  `;
}
