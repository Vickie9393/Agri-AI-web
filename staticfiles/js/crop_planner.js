/* AgriAI — Crop Planner JS */
function getCsrf(){const c=document.cookie.split(';').find(c=>c.trim().startsWith('csrftoken='));return c?c.split('=')[1]:'';}
function showMsg(id,type,text){const el=document.getElementById(id);if(!el)return;el.className=`msg-box ${type}`;el.textContent=text;}

function filterCrops(season, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.crop-card').forEach(card => {
    const show = season === 'all' || card.classList.contains(`season-${season}`);
    card.style.display = show ? '' : 'none';
    if (show) { card.style.animation='none'; card.offsetHeight; card.style.animation='slideUp .4s ease both'; }
  });
}

async function submitCropPlan() {
  const vals = {
    crop_name:        document.getElementById('cpCropName')?.value.trim(),
    variety:          document.getElementById('cpVariety')?.value.trim(),
    season:           document.getElementById('cpSeason')?.value,
    field_area:       document.getElementById('cpArea')?.value,
    sowing_date:      document.getElementById('cpSowDate')?.value,
    expected_harvest: document.getElementById('cpHarvestDate')?.value,
    soil_type:        document.getElementById('cpSoil')?.value,
    irrigation_method:document.getElementById('cpIrrigation')?.value,
    notes:            document.getElementById('cpNotes')?.value.trim(),
  };
  if (!vals.crop_name || !vals.field_area || !vals.sowing_date || !vals.expected_harvest)
    return showMsg('cropMsg','error','⚠️ Fill all required fields');

  const btn = document.querySelector('#addCropModal .btn-primary:last-of-type');
  if (btn) { btn.disabled=true; btn.innerHTML='<i class="fa fa-spinner fa-spin"></i> Saving...'; }

  try {
    const res  = await fetch('/api/crop/add/', {
      method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':getCsrf()},
      body: JSON.stringify({...vals, field_area:parseFloat(vals.field_area)})
    });
    const data = await res.json();
    if (data.success) {
      showMsg('cropMsg','success',`✅ ${data.crop} plan saved!`);
      setTimeout(()=>{ closeModal('addCropModal'); location.reload(); }, 900);
    } else {
      showMsg('cropMsg','error','❌ '+(data.error||'Failed'));
      if(btn){btn.disabled=false;btn.innerHTML='Save Crop Plan 🌾';}
    }
  } catch { showMsg('cropMsg','error','❌ Network error'); if(btn){btn.disabled=false;btn.innerHTML='Save Crop Plan 🌾';} }
}

async function deleteCrop(id, btn) {
  if (!confirm('Delete this crop plan?')) return;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
  try {
    const res  = await fetch(`/api/crop/delete/${id}/`, { headers:{'X-CSRFToken':getCsrf()} });
    const data = await res.json();
    if (data.success) {
      const card = btn.closest('.crop-card');
      card.style.transition = 'all .3s'; card.style.opacity='0'; card.style.transform='scale(.9)';
      setTimeout(() => card.remove(), 320);
    }
  } catch { btn.innerHTML='<i class="fa fa-trash"></i>'; }
}

// Set default dates
document.addEventListener('DOMContentLoaded', () => {
  const today   = new Date().toISOString().split('T')[0];
  const harvest = new Date(Date.now()+120*86400000).toISOString().split('T')[0];
  const s = document.getElementById('cpSowDate');
  const h = document.getElementById('cpHarvestDate');
  if(s&&!s.value) s.value=today;
  if(h&&!h.value) h.value=harvest;
});
