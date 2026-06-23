/* AgriAI — Fertilizer Calculator JS */
function getCsrf(){const c=document.cookie.split(';').find(c=>c.trim().startsWith('csrftoken='));return c?c.split('=')[1]:'';}
function showMsg(id,type,text){const el=document.getElementById(id);if(!el)return;el.className=`msg-box ${type}`;el.textContent=text;setTimeout(()=>{el.className='msg-box';el.textContent='';},4000);}

async function calculateFertilizer() {
  const crop  = document.getElementById('fcCrop')?.value;
  const area  = document.getElementById('fcArea')?.value;
  const soil  = document.getElementById('fcSoil')?.value;
  const stage = document.getElementById('fcStage')?.value;

  if (!crop)        return showMsg('fertMsg','error','⚠️ Select a crop type');
  if (!area||+area<=0) return showMsg('fertMsg','error','⚠️ Enter a valid field area');

  const btn = document.querySelector('.calc-input-card .btn-primary');
  if (btn) { btn.disabled=true; btn.innerHTML='<i class="fa fa-spinner fa-spin"></i> Calculating...'; }

  try {
    const res  = await fetch('/api/fertilizer/calculate/', {
      method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':getCsrf()},
      body: JSON.stringify({ crop_name:crop, field_area:parseFloat(area), soil_type:soil, crop_stage:stage })
    });
    const data = await res.json();
    if (data.success) {
      showMsg('fertMsg','success','✅ Calculation complete!');
      displayFertResult(data);
    } else {
      showMsg('fertMsg','error','❌ '+(data.error||'Calculation failed'));
    }
  } catch { showMsg('fertMsg','error','❌ Network error'); }

  if (btn) { btn.disabled=false; btn.innerHTML='Calculate Fertilizer 🧮'; }
}

function displayFertResult(data) {
  document.getElementById('fertPlaceholder').style.display = 'none';
  const results = document.getElementById('fertResults');
  results.style.display = 'block';

  document.getElementById('nVal').textContent = `${data.nitrogen} kg`;
  document.getElementById('pVal').textContent = `${data.phosphorus} kg`;
  document.getElementById('kVal').textContent = `${data.potassium} kg`;
  document.getElementById('ureaQty').textContent = `${data.urea} kg`;
  document.getElementById('dapQty').textContent  = `${data.dap} kg`;
  document.getElementById('mopQty').textContent  = `${data.mop} kg`;
  document.getElementById('costVal').textContent = `₹${data.estimated_cost.toLocaleString('en-IN')}`;
  document.getElementById('scheduleText').textContent = data.schedule;

  const maxVal = Math.max(data.nitrogen, data.phosphorus, data.potassium, 1);
  setTimeout(() => {
    document.getElementById('nBar').style.width = `${(data.nitrogen/maxVal)*100}%`;
    document.getElementById('pBar').style.width = `${(data.phosphorus/maxVal)*100}%`;
    document.getElementById('kBar').style.width = `${(data.potassium/maxVal)*100}%`;
  }, 100);

  results.scrollIntoView({ behavior:'smooth', block:'nearest' });
}
