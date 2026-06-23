/* AgriAI — Weather JS */
function getCsrf(){const c=document.cookie.split(';').find(c=>c.trim().startsWith('csrftoken='));return c?c.split('=')[1]:'';}

async function searchWeather() {
  const loc = document.getElementById('locationInput')?.value.trim();
  if (!loc) return;
  localStorage.setItem('agriai_location', loc);
  await fetchWeather({ location: loc });
}
async function getGPSWeather() {
  if (!navigator.geolocation) return alert('Geolocation not supported by your browser.');
  showLoading(true);
  navigator.geolocation.getCurrentPosition(
    pos => fetchWeather({ lat:pos.coords.latitude, lon:pos.coords.longitude, location:'Your Location' }),
    ()  => { showLoading(false); alert('Could not get your location. Please search manually.'); }
  );
}
async function fetchWeather({ lat, lon, location }) {
  showLoading(true);
  try {
    const res  = await fetch('/api/weather/', {
      method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':getCsrf()},
      body: JSON.stringify({ lat, lon, location })
    });
    const data = await res.json();
    showLoading(false);
    if (data.success) {
      renderCurrent(data.current);
      renderAdvisory(data.advisory, data.demo);
      renderForecast(data.forecast);
    } else { alert('Could not fetch weather data. Please try again.'); }
  } catch { showLoading(false); alert('Network error. Please try again.'); }
}

function renderCurrent(w) {
  document.getElementById('weatherPlaceholder').style.display = 'none';
  document.getElementById('currentWeatherData').style.display = 'block';
  document.getElementById('weatherMain').style.display = 'grid';

  document.getElementById('cwLocation').textContent  = `${w.location}${w.country?', '+w.country:''}`;
  document.getElementById('cwDate').textContent       = new Date().toLocaleDateString('en-IN',{weekday:'long',day:'numeric',month:'long'});
  document.getElementById('cwTemp').textContent       = `${w.temperature}°C`;
  document.getElementById('cwCondition').textContent  = w.condition;
  document.getElementById('cwFeels').textContent      = w.feels_like;
  document.getElementById('cwHumidity').textContent   = `${w.humidity}%`;
  document.getElementById('cwWind').textContent       = `${w.wind_speed} km/h`;
  document.getElementById('cwPressure').textContent   = `${w.pressure} hPa`;
  document.getElementById('cwVisibility').textContent = `${w.visibility} km`;

  const icon = document.getElementById('cwIcon');
  if (icon) { icon.src = `https://openweathermap.org/img/wn/${w.icon}@2x.png`; icon.onerror=()=>icon.style.display='none'; }
}

function renderAdvisory(advisory, isDemo) {
  const card = document.getElementById('advisoryCard');
  const text = document.getElementById('advisoryText');
  if (card) card.style.display = 'block';
  if (text) text.textContent = advisory + (isDemo ? ' [Demo mode — set OPENWEATHER_API_KEY for live data]' : '');
}

function renderForecast(forecast) {
  const grid        = document.getElementById('forecastGrid');
  const placeholder = document.getElementById('forecastPlaceholder');
  if (!grid) return;
  if (!forecast || !forecast.length) { if(placeholder) placeholder.textContent='Forecast unavailable in demo mode.'; return; }

  if (placeholder) placeholder.style.display = 'none';
  grid.style.display = 'grid';
  grid.innerHTML = '';

  forecast.forEach(day => {
    const date = new Date(day.date).toLocaleDateString('en-IN',{weekday:'short',day:'numeric',month:'short'});
    const d = document.createElement('div');
    d.className = 'forecast-day';
    d.innerHTML = `
      <div class="f-date">${date}</div>
      <img style="width:50px;height:50px" src="https://openweathermap.org/img/wn/${day.icon}.png" alt="${day.condition}" onerror="this.style.display='none'">
      <div class="f-temp">↑${day.temp_max}° ↓${day.temp_min}°</div>
      <div class="f-cond">${day.condition}</div>
      <div class="f-hum">💧 ${day.humidity}%</div>
    `;
    grid.appendChild(d);
  });
}

function showLoading(show) {
  const el = document.getElementById('weatherLoading');
  if (el) el.style.display = show ? 'flex' : 'none';
}

window.addEventListener('load', () => {
  const saved = localStorage.getItem('agriai_location');
  if (saved) { const el = document.getElementById('locationInput'); if(el) el.value=saved; fetchWeather({location:saved}); }
});
