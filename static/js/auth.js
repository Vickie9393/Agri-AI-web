/* ═══════════════════════════════════════
   AgriAI — Auth JavaScript
═══════════════════════════════════════ */

// ── Tab Switching ──
function switchTab(tab) {
  document.querySelectorAll('.tab').forEach((t, i) => {
    t.classList.toggle('active', (tab==='login'&&i===0)||(tab==='signup'&&i===1));
  });
  document.getElementById('loginForm').classList.toggle('active', tab==='login');
  document.getElementById('signupForm').classList.toggle('active', tab==='signup');
  document.getElementById('tabIndicator').classList.toggle('right', tab==='signup');
}

function togglePw(id) {
  const el = document.getElementById(id);
  el.type = el.type === 'password' ? 'text' : 'password';
}

// ── OTP digit auto-focus ──
document.addEventListener('input', e => {
  if (!e.target.classList.contains('otp-digit')) return;
  const inputs = [...e.target.closest('.otp-inputs').querySelectorAll('.otp-digit')];
  const idx = inputs.indexOf(e.target);
  if (e.target.value && idx < inputs.length - 1) inputs[idx + 1].focus();
});
document.addEventListener('keydown', e => {
  if (!e.target.classList.contains('otp-digit') || e.key !== 'Backspace' || e.target.value) return;
  const inputs = [...e.target.closest('.otp-inputs').querySelectorAll('.otp-digit')];
  const idx = inputs.indexOf(e.target);
  if (idx > 0) inputs[idx - 1].focus();
});
// Paste support
document.addEventListener('paste', e => {
  if (!e.target.classList.contains('otp-digit')) return;
  e.preventDefault();
  const text = e.clipboardData.getData('text').replace(/\D/g,'').slice(0,6);
  const inputs = [...e.target.closest('.otp-inputs').querySelectorAll('.otp-digit')];
  inputs.forEach((inp, i) => { if (text[i]) inp.value = text[i]; });
  const last = Math.min(text.length, inputs.length) - 1;
  if (last >= 0) inputs[last].focus();
});

// ── Timers ──
let loginTimerInterval, signupTimerInterval;
function startTimer(spanId, seconds=600) {
  const span = document.getElementById(spanId);
  let rem = seconds;
  const iv = setInterval(() => {
    const m = String(Math.floor(rem/60)).padStart(2,'0');
    const s = String(rem%60).padStart(2,'0');
    if (span) span.textContent = `${m}:${s}`;
    if (--rem < 0) {
      clearInterval(iv);
      if (span) { span.textContent='Expired'; span.style.color='#ef4444'; }
    }
  }, 1000);
  return iv;
}

function showMsg(id, type, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `msg-box ${type}`;
  el.textContent = text;
}
function getOtp(selector) {
  return [...document.querySelectorAll(selector)].map(i=>i.value).join('');
}
function getCsrf() {
  const c = document.cookie.split(';').find(c=>c.trim().startsWith('csrftoken='));
  return c ? c.split('=')[1] : '';
}

// ════════════════════════
// LOGIN FLOW
// ════════════════════════
async function sendLoginOTP() {
  const identifier = document.getElementById('loginIdentifier').value.trim();
  if (!identifier || !identifier.includes('@')) return showMsg('loginMsg','error','⚠️ Enter a valid email address');

  const btn = document.getElementById('loginSendOtpBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Sending OTP...';

  try {
    const res  = await fetch('/api/auth/send-otp/', {
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRFToken':getCsrf()},
      body: JSON.stringify({ identifier, type: 'email', purpose:'login' })
    });
    const data = await res.json();
    if (data.success) {
      showMsg('loginMsg','success', '✅ ' + data.message);
      document.getElementById('loginOtpSection').style.display = 'block';
      document.getElementById('loginVerifyBtn').style.display  = 'flex';
      btn.style.display = 'none';
      clearInterval(loginTimerInterval);
      loginTimerInterval = startTimer('loginTimer');
    } else {
      showMsg('loginMsg','error','❌ '+(data.error||'Failed'));
      btn.disabled = false;
      btn.innerHTML = '<span>Send OTP & Login</span><i class="fa fa-arrow-right"></i>';
    }
  } catch {
    showMsg('loginMsg','error','❌ Network error. Try again.');
    btn.disabled = false;
    btn.innerHTML = '<span>Send OTP & Login</span><i class="fa fa-arrow-right"></i>';
  }
}

async function verifyLoginOTP() {
  const identifier = document.getElementById('loginIdentifier').value.trim();
  const password   = document.getElementById('loginPassword').value;
  const otp        = getOtp('.login-otp-digit');
  if (otp.length < 6) return showMsg('loginMsg','error','⚠️ Enter the complete 6-digit OTP');

  const btn = document.getElementById('loginVerifyBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Verifying...';

  try {
    const res  = await fetch('/api/auth/verify-login/', {
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRFToken':getCsrf()},
      body: JSON.stringify({ identifier, otp, password })
    });
    const data = await res.json();
    if (data.success) {
      showMsg('loginMsg','success','✅ Login successful! Redirecting...');
      setTimeout(() => window.location.href = data.redirect||'/dashboard/', 700);
    } else {
      showMsg('loginMsg','error','❌ '+(data.error||'Invalid OTP'));
      btn.disabled=false; btn.innerHTML='<span>Verify & Sign In</span><i class="fa fa-check"></i>';
    }
  } catch {
    showMsg('loginMsg','error','❌ Network error.'); btn.disabled=false; btn.innerHTML='<span>Verify & Sign In</span><i class="fa fa-check"></i>';
  }
}

// ════════════════════════
// GOOGLE LOGIN HANDLER
// ════════════════════════
async function handleCredentialResponse(response) {
  if (!response.credential) return;
  
  showMsg('loginMsg', 'success', '🔄 Verifying Google Login...');
  try {
    const res = await fetch('/api/auth/google/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({ credential: response.credential })
    });
    const data = await res.json();
    if (data.success) {
      showMsg('loginMsg', 'success', '✅ Google Login successful! Redirecting...');
      setTimeout(() => window.location.href = data.redirect || '/dashboard/', 700);
    } else {
      showMsg('loginMsg', 'error', '❌ ' + (data.error || 'Google Login failed'));
    }
  } catch (err) {
    showMsg('loginMsg', 'error', '❌ Network error during Google login.');
  }
}

// ════════════════════════
// SIGNUP FLOW
// ════════════════════════
async function sendSignupOTP() {
  const name     = document.getElementById('signupName').value.trim();
  const username = document.getElementById('signupUsername').value.trim();
  const email    = document.getElementById('signupEmail').value.trim();
  const password = document.getElementById('signupPassword').value;

  if (!name||!username||!email||!password)
    return showMsg('signupMsg','error','⚠️ Please fill all required fields');
  if (password.length < 8)
    return showMsg('signupMsg','error','⚠️ Password must be at least 8 characters');

  const btn = document.getElementById('signupSendOtpBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Sending OTP...';

  try {
    const res  = await fetch('/api/auth/send-otp/', {
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRFToken':getCsrf()},
      body: JSON.stringify({ identifier:email, type:'email', purpose:'register' })
    });
    const data = await res.json();
    if (data.success) {
      showMsg('signupMsg','success','✅ '+data.message);
      document.getElementById('signupOtpSection').style.display = 'block';
      document.getElementById('signupVerifyBtn').style.display  = 'flex';
      btn.style.display = 'none';
      clearInterval(signupTimerInterval);
      signupTimerInterval = startTimer('signupTimer');
    } else {
      showMsg('signupMsg','error','❌ '+(data.error||'Failed'));
      btn.disabled=false; btn.innerHTML='<span>Send OTP</span><i class="fa fa-paper-plane"></i>';
    }
  } catch {
    showMsg('signupMsg','error','❌ Network error.');
    btn.disabled=false; btn.innerHTML='<span>Send OTP</span><i class="fa fa-paper-plane"></i>';
  }
}

async function verifySignupOTP() {
  const otp = getOtp('.signup-otp');
  if (otp.length < 6) return showMsg('signupMsg','error','⚠️ Enter the 6-digit OTP');

  const btn = document.getElementById('signupVerifyBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Creating Account...';

  try {
    const res  = await fetch('/api/auth/verify-register/', {
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRFToken':getCsrf()},
      body: JSON.stringify({
        identifier: document.getElementById('signupEmail').value.trim(),
        otp,
        username:  document.getElementById('signupUsername').value.trim(),
        password:  document.getElementById('signupPassword').value,
        full_name: document.getElementById('signupName').value.trim(),
        mobile:    '',
      })
    });
    const data = await res.json();
    if (data.success) {
      showMsg('signupMsg','success','🌱 Account created! Redirecting...');
      setTimeout(() => window.location.href = data.redirect||'/dashboard/', 900);
    } else {
      showMsg('signupMsg','error','❌ '+(data.error||'Registration failed'));
      btn.disabled=false; btn.innerHTML='<span>Create Account</span><i class="fa fa-seedling"></i>';
    }
  } catch {
    showMsg('signupMsg','error','❌ Network error.');
    btn.disabled=false; btn.innerHTML='<span>Create Account</span><i class="fa fa-seedling"></i>';
  }
}
