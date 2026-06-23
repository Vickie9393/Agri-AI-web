/* ═══════════════════════════════════════
   AgriAI — Base JavaScript
   Nav · Chatbot · Contact · Utilities
═══════════════════════════════════════ */

// ════════════════════
// UTILS
// ════════════════════
function getCsrf() {
  const c = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return c ? c.split('=')[1] : '';
}
function openModal(id)  { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }

document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) e.target.classList.remove('open');
});

// ════════════════════
// NAVBAR
// ════════════════════
window.addEventListener('scroll', () => {
  document.getElementById('topNav')?.classList.toggle('scrolled', window.scrollY > 8);
});

function toggleUserMenu() {
  document.getElementById('userDropdown')?.classList.toggle('open');
}
document.addEventListener('click', e => {
  if (!e.target.closest('.user-pill') && !e.target.closest('.user-dropdown')) {
    document.getElementById('userDropdown')?.classList.remove('open');
  }
});

function toggleMobileNav() {
  document.getElementById('navLinks')?.classList.toggle('open');
  document.getElementById('hamburger')?.classList.toggle('active');
}

// ════════════════════
// CHATBOT
// ════════════════════
let chatContext  = 'general';
let pendingImage = null;
let chatOpen     = false;

function toggleChatbot() {
  chatOpen = !chatOpen;
  document.getElementById('chatbotPanel')?.classList.toggle('open', chatOpen);
  if (chatOpen) setTimeout(() => document.getElementById('chatInput')?.focus(), 300);
}

function setContext(ctx, btn) {
  chatContext = ctx;
  document.querySelectorAll('.ctx-tab').forEach(t => t.classList.remove('active'));
  btn?.classList.add('active');
  const imgZone = document.getElementById('chatImageZone');
  if (imgZone) imgZone.style.display = ctx === 'disease' ? 'block' : 'none';
}

function toggleImageUpload() {
  const z = document.getElementById('chatImageZone');
  if (z) z.style.display = z.style.display === 'none' ? 'block' : 'none';
}

function handleChatImage(input) {
  const file = input.files[0];
  if (!file) return;
  pendingImage = file;
  const reader = new FileReader();
  reader.onload = e => {
    const p = document.getElementById('chatImagePreview');
    if (p) p.innerHTML = `<img src="${e.target.result}" style="max-width:100%;max-height:90px;border-radius:8px;margin-top:.4rem">`;
  };
  reader.readAsDataURL(file);
  appendMsg('user', `📸 Image ready: ${file.name}`);
}

function appendMsg(role, text) {
  const box = document.getElementById('chatMessages');
  if (!box) return;
  const d = document.createElement('div');
  d.className = `chat-msg ${role}`;
  d.innerHTML = `
    <div class="msg-avatar">${role==='bot'?'🤖':'👨‍🌾'}</div>
    <div class="msg-bubble">${text.replace(/\n/g,'<br>').replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')}</div>
  `;
  box.appendChild(d);
  box.scrollTop = box.scrollHeight;
}

function showTyping() {
  const box = document.getElementById('chatMessages');
  if (!box) return;
  const d = document.createElement('div');
  d.id = 'chatTyping'; d.className = 'chat-msg bot';
  d.innerHTML = `<div class="msg-avatar">🤖</div>
    <div class="msg-bubble" style="padding:.7rem 1rem">
      <span style="display:flex;gap:5px;align-items:center">
        ${[0,.18,.35].map(d=>`<span style="width:8px;height:8px;background:var(--green-light);border-radius:50%;animation:dotB 1s ${d}s ease infinite"></span>`).join('')}
      </span>
    </div>`;
  if (!document.getElementById('dotBStyle')) {
    const s = document.createElement('style');
    s.id = 'dotBStyle';
    s.textContent = '@keyframes dotB{0%,80%,100%{transform:scale(1)}40%{transform:scale(1.4)}}';
    document.head.appendChild(s);
  }
  box.appendChild(d);
  box.scrollTop = box.scrollHeight;
}
function removeTyping() { document.getElementById('chatTyping')?.remove(); }

async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const msg   = input?.value.trim();
  if (!msg && !pendingImage) return;

  const display = msg || 'Please analyse this crop image.';
  appendMsg('user', display);
  if (input) input.value = '';
  showTyping();

  try {
    let res;
    if (pendingImage) {
      const fd = new FormData();
      fd.append('message', display);
      fd.append('context', chatContext);
      fd.append('image',   pendingImage);
      res = await fetch('/api/chatbot/', { method:'POST', headers:{'X-CSRFToken':getCsrf()}, body:fd });
      pendingImage = null;
      const p = document.getElementById('chatImagePreview');
      if (p) p.innerHTML = '';
    } else {
      res = await fetch('/api/chatbot/', {
        method:'POST',
        headers:{'Content-Type':'application/json','X-CSRFToken':getCsrf()},
        body:JSON.stringify({ message:msg, context:chatContext })
      });
    }
    const data = await res.json();
    removeTyping();
    appendMsg('bot', data.response || '🌿 Something went wrong, please try again.');
  } catch {
    removeTyping();
    appendMsg('bot', '🌿 Connection issue. Please try again in a moment!');
  }
}

document.addEventListener('keypress', e => {
  if (e.target.id === 'chatInput' && e.key === 'Enter') sendChatMessage();
});

function clearChat() {
  const box = document.getElementById('chatMessages');
  if (box) box.innerHTML = `<div class="chat-msg bot"><div class="msg-avatar">🤖</div><div class="msg-bubble">🌿 Chat cleared! How can I help with your farming today? 🚜</div></div>`;
}

// ════════════════════
// CONTACT
// ════════════════════
async function submitContact() {
  const name    = document.getElementById('contactName')?.value.trim();
  const email   = document.getElementById('contactEmail')?.value.trim();
  const subject = document.getElementById('contactSubject')?.value.trim();
  const msg     = document.getElementById('contactMsg')?.value.trim();

  if (!name||!email||!subject||!msg) {
    showContactResult('error','⚠️ Please fill all fields'); return;
  }

  const btn = document.querySelector('.btn-submit');
  if (btn) { btn.disabled=true; btn.innerHTML='Sending... <i class="fa fa-spinner fa-spin"></i>'; }

  try {
    const res  = await fetch('/api/contact/', {
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRFToken':getCsrf()},
      body:JSON.stringify({ name, email, subject, message:msg })
    });
    const data = await res.json();
    if (data.success) {
      showContactResult('success','✅ '+data.message);
      ['contactName','contactEmail','contactSubject','contactMsg'].forEach(id => { const el = document.getElementById(id); if(el) el.value=''; });
    } else {
      showContactResult('error','❌ '+(data.error||'Failed to send'));
    }
  } catch {
    showContactResult('error','❌ Network error. Please try again.');
  }
  if (btn) { btn.disabled=false; btn.innerHTML='Send Message <i class="fa fa-paper-plane"></i>'; }
}

function showContactResult(type, text) {
  const el = document.getElementById('contactResult');
  if (!el) return;
  el.className = `msg-box ${type}`; el.textContent = text;
  setTimeout(() => { el.className='msg-box'; el.textContent=''; }, 5000);
}

// ════════════════════
// ANIMATIONS
// ════════════════════
const observer = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) e.target.style.animationPlayState = 'running'; });
}, { threshold: 0.08 });

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.animate-in').forEach(el => {
    el.style.animationPlayState = 'paused';
    observer.observe(el);
  });
});
