# -*- coding: utf-8 -*-
"""
Sistema de Turnos de Espera
8 tecnicos, reasignacion, activar/desactivar, voz en espanol.
Tecnico ve solo su ventanilla. Admin imprime informe diario.
"""

import threading
import time
from datetime import date
from flask import Flask, render_template_string, request, jsonify, redirect, session

app = Flask(__name__)
app.secret_key = 'turnos-secret-key-cambiar'

admins = ['Carmen Cruz', 'Edwin Ovando', 'Carmen Elena']

with open('static/1.jpg', 'rb') as f: LOGO1_B64 = __import__('base64').b64encode(f.read()).decode()
with open('static/2.png', 'rb') as f: LOGO2_B64 = __import__('base64').b64encode(f.read()).decode()
with open('static/3.webp', 'rb') as f: LOGO3_B64 = __import__('base64').b64encode(f.read()).decode()

lock = threading.Lock()
state = {
    "next": 1,
    "pending": [[] for _ in range(8)],
    "active": [True] * 8,
    "attended": [[] for _ in range(8)],
    "day": str(date.today()),
    "last_event": None,
    "attendance": {},
}

def broadcast(event):
    state["last_event"] = event

def check_day():
    hoy = str(date.today())
    if state["day"] != hoy:
        state["day"] = hoy
        state["pending"] = [[] for _ in range(8)]
        state["attended"] = [[] for _ in range(8)]

# ─── PANTALLA PUBLICA ───────────────────────────────────────────
DISPLAY_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5">
<title>Turnos en Espera</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',sans-serif; background:#0a0a0a; color:#fff; min-height:100vh; min-height:100dvh; }
  .top { background:#0d0d2b; padding:clamp(8px,2vw,16px) clamp(12px,4vw,30px); display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #1a3a8a; }
  .top .logo { height:clamp(28px,5vw,45px); vertical-align:middle; }
  .top #clock { font-size:clamp(1em,3vw,1.5em); color:#60a5fa; font-weight:bold; }
  .waiting { background:#0d0d2b; padding:clamp(6px,1.5vw,12px) 15px; text-align:center; font-size:clamp(1.1em,3vw,1.6em); border-bottom:1px solid #1a3a8a; }
  .waiting b { color:#3b82f6; font-size:1.3em; }
  .anuncio { text-align:center; padding:clamp(15px,3vw,35px) 10px; background:linear-gradient(135deg,#060620,#0d0d2b); min-height:35vh; min-height:35dvh; display:flex; flex-direction:column; justify-content:center; }
  .anuncio .msg { font-size:clamp(1.8em,5vw,4em); font-weight:bold; color:#fff; line-height:1.1; margin-bottom:5px; }
  .anuncio .num { font-size:clamp(6em,30vw,26em); font-weight:900; color:#fbbf24; line-height:0.85; text-shadow:0 0 40px rgba(251,191,36,.5); }
  .anuncio .sub { font-size:clamp(1.5em,4vw,3.5em); color:#60a5fa; margin-top:clamp(5px,1.5vw,15px); font-weight:bold; }
  .anuncio.idle .num { color:#1e3a5f; font-size:clamp(3em,10vw,7em); text-shadow:none; }
  .anuncio.idle .msg, .anuncio.idle .sub { color:#4a6a8a; }
  .btn-turno { display:block; width:min(320px,90%); margin:clamp(8px,1.5vw,20px) auto; padding:clamp(12px,2vw,20px); background:#3b82f6; color:#fff; border:none; border-radius:clamp(10px,2vw,15px); font-size:clamp(1.2em,3vw,1.6em); font-weight:bold; cursor:pointer; }
  .btn-turno:hover { background:#2563eb; }
  .btn-turno:active { transform:scale(0.97); }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:clamp(8px,1.5vw,20px); padding:clamp(10px,2vw,30px); }
  .win { background:#0d0d2b; border-radius:clamp(12px,2vw,20px); padding:clamp(12px,2vw,20px); text-align:center; border:3px solid #1a3a8a; min-height:120px; display:flex; flex-direction:column; justify-content:center; }
  .win.active { border-color:#3b82f6; }
  .win.off { opacity:0.35; }
  .win .num { font-size:clamp(1.8em,4vw,2.8em); font-weight:bold; color:#ef4444; }
  .win .lbl { font-size:clamp(0.75em,1.8vw,1em); color:#94a3b8; margin-top:6px; }
  .win .empty { color:#4a6a8a; font-size:clamp(1.5em,3vw,2.2em); }
  .win .count { font-size:clamp(0.7em,1.5vw,0.9em); color:#ef4444; margin-top:4px; }
  .win .attended { font-size:clamp(0.7em,1.5vw,0.9em); color:#22c55e; margin-top:2px; }
</style>
</head>
<body>
  <div class="top">
    <img class="logo" src="data:image/jpeg;base64,__LOGO1__" alt="Logo">
    <div id="clock"></div>
  </div>
  <div class="waiting">En espera: <b id="waitingCount">0</b> personas</div>
  <button class="btn-turno" onclick="tomarTurno()">🎫 Tomar Turno</button>

  <div class="anuncio idle" id="anuncio">
    <div class="msg">Bienvenido</div>
    <div class="num" id="anum">---</div>
    <div class="sub" id="asub">Espere a ser llamado</div>
  </div>

  <div class="grid" id="grid"></div>

<script>
  const techNames = ['Mauricio Amaya', 'Julio Castillo', 'Jorge Hernandez', 'Yesica Bonilla', 'Alba Zelaya', 'Manuel Herrera', 'William Espiñal', 'Rene Quintanilla'];
  let ultimoTs = null;
  function tomarTurno() {
    fetch('/api/tomar_turno', {method:'POST'}).then(r=>r.json()).then(d=>{
      if (d.success) {
        document.getElementById('anuncio').className = 'anuncio';
        document.getElementById('anum').textContent = d.num;
        document.getElementById('asub').textContent = 'Tecnico ' + techNames[d.ventanilla-1];
        document.querySelector('#anuncio .msg').textContent = 'Usuario ' + d.num + ', el tecnico ' + techNames[d.ventanilla-1] + ' le atendera';
        hablar(d.num, techNames[d.ventanilla-1]);
      }
    });
  }
  function hablar(num, tec) {
    if ('speechSynthesis' in window) {
      const u = new SpeechSynthesisUtterance('Usuario ' + num + ', el tecnico ' + tec + ' le atendera');
      u.lang = 'es-ES'; u.rate = 0.85;
      window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
    }
  }
  function totalEspera(data) {
    let total = 0;
    for (let i = 0; i < 8; i++) total += data.pending[i].length;
    return total;
  }
  function render(data) {
    document.getElementById('waitingCount').textContent = totalEspera(data);
    const grid = document.getElementById('grid'); grid.innerHTML = '';
    for (let i = 0; i < 8; i++) {
      const pend = data.pending[i]; const on = data.active[i];
      const div = document.createElement('div');
      div.className = 'win ' + (on ? 'active' : 'off');
      const atend = (data.attended[i] || []).length;
      let html = '';
      if (pend.length > 0) {
        html = '<div class="num">' + pend[0] + '</div>';
      } else {
        html = '<div class="empty">---</div>';
      }
      html += '<div class="lbl">' + techNames[i] + (on ? '' : ' (off)') + '</div>';
      if (pend.length > 0) html += '<div class="count">En espera: ' + pend.length + '</div>';
      if (atend > 0) html += '<div class="attended">Atendidos: ' + atend + '</div>';
      div.innerHTML = html;
      grid.appendChild(div);
    }
  }
  function actualizar() {
    fetch('/api/estado').then(r=>r.json()).then(data=>{
      render(data);
      const ev = data.last_event;
      if (ev && ev.type === 'llamada' && ev.ts !== ultimoTs) {
        ultimoTs = ev.ts;
        document.getElementById('anuncio').className = 'anuncio';
        document.getElementById('anum').textContent = ev.num;
        document.getElementById('asub').textContent = 'Tecnico ' + techNames[ev.ventanilla-1];
        document.querySelector('#anuncio .msg').textContent = 'Usuario ' + ev.num + ', el tecnico ' + techNames[ev.ventanilla-1] + ' le atendera';
        hablar(ev.num, techNames[ev.ventanilla-1]);
      }
    });
  }
  setInterval(()=>{ document.getElementById('clock').textContent = new Date().toLocaleTimeString('es-ES'); }, 1000);
  actualizar(); setInterval(actualizar, 1000);
</script>
</body>
</html>
"""

# ─── TECNICOS ─────────────────────────────────────────────────
techNames = ['Mauricio Amaya', 'Julio Castillo', 'Jorge Hernandez', 'Yesica Bonilla', 'Alba Zelaya', 'Manuel Herrera', 'William Espiñal', 'Rene Quintanilla']

TECH_LOGIN = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Acceso Tecnico</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Share Tech Mono','Courier New',monospace; background:radial-gradient(ellipse at center,#050510 0%,#000 100%); color:#fff; min-height:100vh; display:flex; align-items:center; justify-content:center; overflow:hidden; }
  body::before { content:''; position:fixed; inset:0; background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(59,130,246,0.04) 2px,rgba(59,130,246,0.04) 4px); pointer-events:none; }
  .card { position:relative; background:linear-gradient(135deg,#0a0a2e,#050510); border-radius:16px; padding:45px 40px 35px; width:400px; border:1px solid rgba(59,130,246,0.25); box-shadow:0 0 40px rgba(59,130,246,0.08),inset 0 0 60px rgba(59,130,246,0.03); }
  .card::after { content:''; position:absolute; top:-1px; left:20%; right:20%; height:2px; background:linear-gradient(90deg,transparent,#3b82f6,transparent); }
  .card .logo { display:block; width:120px; margin:0 auto 10px; filter:drop-shadow(0 0 15px rgba(59,130,246,0.3)); }
  .card h1 { color:#3b82f6; font-size:1.3em; letter-spacing:3px; text-transform:uppercase; text-shadow:0 0 20px rgba(59,130,246,0.3); margin-bottom:5px; }
  .sub { color:#4a6a8a; font-size:0.8em; letter-spacing:2px; margin-bottom:25px; }
  .card input { width:100%; padding:14px 18px; border-radius:8px; border:1px solid #1a3a8a; background:#050510; color:#3b82f6; font-family:inherit; font-size:1.1em; text-align:center; margin-bottom:15px; letter-spacing:1px; transition:.3s; }
  .card input:focus { outline:none; border-color:#3b82f6; box-shadow:0 0 20px rgba(59,130,246,0.15); }
  .card input::placeholder { color:#1a3a8a; letter-spacing:1px; }
  .card button { width:100%; padding:14px; background:linear-gradient(135deg,#2563eb,#1d4ed8); color:#fff; border:none; border-radius:8px; font-family:inherit; font-size:1.1em; font-weight:bold; cursor:pointer; letter-spacing:2px; text-transform:uppercase; transition:.3s; box-shadow:0 0 20px rgba(59,130,246,0.15); }
  .card button:hover { background:linear-gradient(135deg,#3b82f6,#2563eb); box-shadow:0 0 30px rgba(59,130,246,0.3); transform:translateY(-2px); }
  .error { color:#ef4444; margin-top:12px; font-size:0.9em; text-shadow:0 0 10px rgba(239,68,68,0.3); }
  .card a { display:block; margin-top:20px; color:#1a3a8a; text-decoration:none; font-size:0.85em; transition:.3s; }
  .card a:hover { color:#4a6a8a; }
  .scanline { position:fixed; inset:0; background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,0.2) 3px,rgba(0,0,0,0.2) 4px); pointer-events:none; }
</style>
</head>
<body>
  <div class="scanline"></div>
  <div class="card">
    <img class="logo" src="data:image/webp;base64,__LOGO3__" alt="Logo">
    <h1>Acceso Técnico</h1>
    <div class="sub">SISTEMA DE TURNOS v2.0</div>
    <form method="POST" action="/tecnico">
      <input type="text" name="username" placeholder="INGRESE SU NOMBRE" required autofocus>
      <button type="submit">INGRESAR</button>
    </form>
    {% if error %}<div class="error">! {{ error }} !</div>{% endif %}
  </div>
</body>
</html>
"""

# ─── VISTA DEL TECNICO (solo su ventanilla) ───────────────────
TECH_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__NAME__</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Share Tech Mono','Courier New',monospace; background:radial-gradient(ellipse at center,#050510 0%,#000 100%); min-height:100vh; padding:20px; overflow-x:hidden; display:flex; align-items:center; justify-content:center; }
  body::before { content:''; position:fixed; inset:0; background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(59,130,246,0.04) 2px,rgba(59,130,246,0.04) 4px); pointer-events:none; }
  .scanline { position:fixed; inset:0; background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,0.2) 3px,rgba(0,0,0,0.2) 4px); pointer-events:none; }
  .card { max-width:520px; width:100%; margin:0; background:linear-gradient(135deg,#0a0a2e,#050510); border-radius:16px; padding:30px; text-align:center; border:1px solid rgba(59,130,246,0.2); box-shadow:0 0 40px rgba(59,130,246,0.06),inset 0 0 60px rgba(59,130,246,0.02); position:relative; }
  .card::after { content:''; position:absolute; top:-1px; left:20%; right:20%; height:2px; background:linear-gradient(90deg,transparent,#3b82f6,transparent); }
  .header { display:flex; align-items:center; justify-content:center; gap:12px; margin-bottom:5px; }
  .header .icon { font-size:2em; filter:drop-shadow(0 0 10px rgba(59,130,246,0.3)); }
  .header .name { color:#3b82f6; font-size:1.2em; letter-spacing:2px; text-shadow:0 0 15px rgba(59,130,246,0.2); }
  .status-bar { display:flex; justify-content:space-between; align-items:center; background:rgba(59,130,246,0.07); border:1px solid rgba(59,130,246,0.15); border-radius:8px; padding:12px 15px; margin:15px 0; }
  .status-bar .label { color:#b0c4d8; font-size:0.9em; letter-spacing:1px; }
  .status-bar .label strong { color:#3b82f6; }
  .pend-list { text-align:left; margin:10px 0; max-height:260px; overflow-y:auto; scrollbar-width:thin; scrollbar-color:#3b82f6 transparent; }
  .pend-list::-webkit-scrollbar { width:4px; }
  .pend-list::-webkit-scrollbar-thumb { background:#3b82f6; border-radius:2px; }
  .pend-item { display:flex; justify-content:space-between; align-items:center; padding:12px 16px; background:rgba(59,130,246,0.03); border-radius:8px; margin-bottom:6px; border:1px solid rgba(59,130,246,0.08); transition:.3s; }
  .pend-item:hover { border-color:rgba(59,130,246,0.2); background:rgba(59,130,246,0.06); }
  .pend-item .pos { color:#8ab4c8; font-size:0.9em; }
  .pend-item .num { font-size:1.6em; font-weight:bold; text-shadow:0 0 12px rgba(59,130,246,0.25); }
  .pend-item.pending .num { color:#ef4444; }
  .pend-item.attended .num { color:#22c55e; }
  .pend-item.attended { opacity:0.7; }
  .empty-pend { color:#4a6a8a; text-align:center; padding:25px; font-size:1em; letter-spacing:1px; }
  .empty-pend .led { display:inline-block; width:8px; height:8px; background:#4a6a8a; border-radius:50%; margin-right:8px; vertical-align:middle; animation:blink 2s infinite; }
  @keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
  .btn { width:100%; padding:16px; background:linear-gradient(135deg,#2563eb,#1d4ed8); color:#fff; border:none; border-radius:8px; font-family:inherit; font-size:1.2em; font-weight:bold; cursor:pointer; letter-spacing:2px; text-transform:uppercase; transition:.3s; box-shadow:0 0 20px rgba(59,130,246,0.12); margin-top:12px; }
  .btn:hover:not(:disabled) { background:linear-gradient(135deg,#3b82f6,#2563eb); box-shadow:0 0 30px rgba(59,130,246,0.25); transform:translateY(-2px); }
  .btn:disabled { background:#0a0a2e; color:#4a6a8a; cursor:not-allowed; box-shadow:none; border:1px solid #1a3a8a; }
  .btn-off { background:#0a0a2e; color:#4a6a8a; cursor:not-allowed; box-shadow:none; border:1px solid #1a3a8a; }
  .off-msg { color:#ef4444; font-size:0.9em; margin:12px 0; text-shadow:0 0 10px rgba(239,68,68,0.2); }
  .back { display:block; text-align:center; margin-top:18px; color:#4a6a8a; text-decoration:none; font-size:0.85em; letter-spacing:1px; transition:.3s; }
  .back:hover { color:#b0c4d8; }
  .divider { height:1px; background:linear-gradient(90deg,transparent,rgba(59,130,246,0.15),transparent); margin:10px 0; }
  .asist-tech { margin:8px 0; display:flex; align-items:center; justify-content:center; gap:6px; flex-wrap:wrap; }
  .asist-tech .lbl { color:#4a6a8a; font-size:0.8em; letter-spacing:1px; width:100%; text-align:center; margin-bottom:4px; }
  .asist-tech button { padding:4px 10px; border-radius:6px; border:2px solid #1a3a8a; background:#050510; color:#4a6a8a; font-family:inherit; font-size:0.75em; cursor:pointer; transition:.3s; letter-spacing:1px; }
  .asist-tech button.on.sede { border-color:#3b82f6; background:rgba(59,130,246,0.1); color:#3b82f6; }
  .asist-tech button.on.movil { border-color:#f59e0b; background:rgba(245,158,11,0.1); color:#f59e0b; }
  .asist-tech button.on.mision { border-color:#8b5cf6; background:rgba(139,92,246,0.1); color:#8b5cf6; }
  .asist-tech button.on.ausente { border-color:#ef4444; background:rgba(239,68,68,0.1); color:#ef4444; }
  .asist-tech button.on.incapacidad { border-color:#f97316; background:rgba(249,115,22,0.1); color:#f97316; }
  .asist-tech button.on.consulta { border-color:#14b8a6; background:rgba(20,184,166,0.1); color:#14b8a6; }
</style>
</head>
<body>
  <div class="scanline"></div>
  <div class="card" id="card">
    <div class="header">
      <span class="icon">🖥️</span>
      <span class="name">__NAME__</span>
    </div>
    <div class="divider"></div>
    <div class="status-bar">
      <span class="label">👤 Tienes <strong id="count">0</strong> usuarios en espera</span>
    </div>
    <div class="divider"></div>
    <div class="asist-tech" id="asistTech">
      <div class="lbl">📍 MI ASISTENCIA:</div>
    </div>
    <div class="divider"></div>

    <div class="pend-list" id="pendList">
      <div class="empty-pend"><span class="led"></span>SIN TURNOS EN ESPERA</div>
    </div>
    <div class="divider"></div>
    <div class="pend-list" id="attendedList" style="max-height:160px;">
      <div class="empty-pend" style="color:#22c55e;">SIN ATENDIDOS</div>
    </div>
    <div id="offmsg"></div>
    <button class="btn" id="btnAtender" onclick="atender()">▶ ATENDER SIGUIENTE</button>
  </div>
  <a href="/logout-tecnico" class="back">[ ← CAMBIAR TÉCNICO ]</a>

<script>
  const v = __V__;
  const asistOpts = [
    {key:'sede', lbl:'🏢 Sede', cls:'sede'},
    {key:'movil', lbl:'🚐 Móvil', cls:'movil'},
    {key:'mision', lbl:'🏛️ M. Oficial', cls:'mision'},
    {key:'ausente', lbl:'❌ Ausente', cls:'ausente'},
    {key:'incapacidad', lbl:'🏥 Incapacidad', cls:'incapacidad'},
    {key:'consulta', lbl:'📋 Consulta', cls:'consulta'}
  ];
  function initAsist() {
    fetch('/api/estado').then(r=>r.json()).then(data => {
      const val = (data.attendance_today || {})[v-1] || 'sede';
      renderAsist(val);
    });
  }
  function renderAsist(val) {
    const container = document.getElementById('asistTech');
    let html = '<div class="lbl">📍 MI ASISTENCIA:</div>';
    asistOpts.forEach(o => {
      html += '<button class="' + (val === o.key ? 'on ' + o.cls : '') + '" onclick="setAsist(\'' + o.key + '\')">' + o.lbl + '</button>';
    });
    container.innerHTML = html;
  }
  function setAsist(tipo) {
    const obj = {}; obj[v-1] = tipo;
    fetch('/api/asistencia', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({registro: obj})})
      .then(r=>r.json()).then(d => {
        if (d.success) { renderAsist(tipo); }
      });
  }
  function render(data) {
    const pend = data.pending[v-1]; const atend = data.attended[v-1] || [];
    const on = data.active[v-1];
    document.getElementById('count').textContent = pend.length;
    const list = document.getElementById('pendList');
    list.innerHTML = '';
    if (pend.length === 0) {
      list.innerHTML = '<div class="empty-pend"><span class="led"></span>SIN TURNOS EN ESPERA</div>';
    } else {
      pend.forEach((n, idx) => {
        const item = document.createElement('div');
        item.className = 'pend-item pending';
        item.innerHTML = '<span class="pos">#' + (idx+1) + '</span><span class="num">' + n + '</span>';
        list.appendChild(item);
      });
    }
    const alist = document.getElementById('attendedList');
    alist.innerHTML = '';
    if (atend.length === 0) {
      alist.innerHTML = '<div class="empty-pend" style="color:#22c55e;">SIN ATENDIDOS</div>';
    } else {
      atend.slice(-10).reverse().forEach((n, idx) => {
        const item = document.createElement('div');
        item.className = 'pend-item attended';
        item.innerHTML = '<span class="pos">#' + (atend.length - idx) + '</span><span class="num">' + n + '</span>';
        alist.appendChild(item);
      });
    }
    const btn = document.getElementById('btnAtender');
    const off = document.getElementById('offmsg');
    if (!on) {
      btn.disabled = true; btn.textContent = '⚙ INACTIVO';
      btn.className = 'btn-off';
      off.innerHTML = '<div class="off-msg">! SISTEMA INACTIVO - Contacte al administrador !</div>';
    } else {
      btn.disabled = (pend.length === 0);
      btn.textContent = pend.length > 0 ? '▶ ATENDER SIGUIENTE' : '⏻ ESPERANDO TURNOS';
      btn.className = 'btn';
      off.innerHTML = '';
    }
  }
  function atender() {
    fetch('/api/atender_siguiente/' + v, {method:'POST'}).then(r=>r.json()).then(d=>{
      if (!d.success && d.error) alert(d.error);
      actualizar();
    });
  }
  function actualizar() { fetch('/api/estado').then(r=>r.json()).then(render); }
  initAsist(); actualizar(); setInterval(actualizar, 1500);
</script>
</body>
</html>
"""

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Acceso - Turnos</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',sans-serif; background:#0a0a0a; color:#fff; min-height:100vh; display:flex; align-items:center; justify-content:center; }
  .card { background:#0d0d2b; border-radius:20px; padding:40px; text-align:center; width:360px; border:2px solid #1a3a8a; }
  .card .logo { height:60px; margin-bottom:15px; }
  .card h1 { color:#3b82f6; margin-bottom:20px; font-size:1.3em; }
  .card input { width:100%; padding:14px; border-radius:10px; border:2px solid #1a3a8a; background:#0a0a0a; color:#fff; font-size:1.1em; text-align:center; margin-bottom:15px; }
  .card input:focus { outline:none; border-color:#3b82f6; }
  .card button { width:100%; padding:14px; background:#3b82f6; color:#fff; border:none; border-radius:10px; font-size:1.2em; font-weight:bold; cursor:pointer; }
  .card button:hover { background:#2563eb; }
  .error { color:#ef4444; margin-top:10px; }
</style>
</head>
<body>
  <div class="card">
    <img class="logo" src="data:image/png;base64,__LOGO2__" alt="Logo">
    <h1>Sistema de Turnos</h1>
    <p style="color:#4a6a8a; margin-bottom:20px;">Ingrese su nombre de usuario</p>
    <form method="POST">
      <input type="text" name="username" placeholder="Usuario" required autofocus>
      <button type="submit">Ingresar</button>
    </form>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
  </div>
</body>
</html>
"""

# ─── PANEL CENTRAL ─────────────────────────────────────────────
CENTRAL_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Panel Central - Turnos</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',sans-serif; background:#0a0a0a; min-height:100vh; padding:20px; }
  .top { text-align:center; margin-bottom:15px; }
  .top .logo { height:50px; margin-bottom:5px; }
  h1 { color:#3b82f6; font-size:1.3em; }
  .top .user { color:#4a6a8a; font-size:0.9em; margin-top:3px; }
  .nav-grid { display:flex; justify-content:center; gap:12px; margin:0 auto 25px; max-width:650px; }
  .nav-card { width:240px; background:#0d0d2b; border-radius:15px; padding:20px; text-align:center; text-decoration:none; color:#fff; border:2px solid #1a3a8a; transition:.3s; cursor:pointer; display:block; }
  .nav-card:hover { transform:scale(1.04); }
  .nav-card.pub:hover { border-color:#3b82f6; background:#0a0a2e; }
  .nav-card.tec:hover { border-color:#60a5fa; background:#0d0d2b; }
  .nav-card .icon { font-size:2em; margin-bottom:5px; }
  .nav-card .tit { font-size:1.1em; font-weight:bold; }
  .section-title { text-align:center; font-size:1.2em; color:#3b82f6; margin:20px 0 10px; font-weight:bold; border-top:2px solid #1a3a8a; padding-top:20px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:15px; max-width:1100px; margin:0 auto 20px; }
  .card { background:#0d0d2b; border-radius:15px; padding:20px; text-align:center; border:2px solid #1a3a8a; }
  .card.off { opacity:0.5; }
  .card .vnum { font-size:1em; color:#e2e8f0; font-weight:bold; }
  .card .current { font-size:2.5em; font-weight:bold; color:#3b82f6; margin:8px 0; }
  .card .current.none { color:#4a6a8a; }
  .card .pend { color:#60a5fa; font-weight:bold; font-size:0.9em; }
  .card .att { color:#3b82f6; font-weight:bold; }
  .btn { width:100%; padding:10px; background:#2563eb; color:#fff; border:none; border-radius:10px; font-size:1em; cursor:pointer; margin-top:6px; }
  .btn-off { background:#1a3a8a; }
  .actions { text-align:center; margin-bottom:20px; }
  .actions button { padding:10px 20px; margin:0 5px; border:none; border-radius:10px; cursor:pointer; font-weight:bold; }
  .btn-print { background:#3b82f6; color:#fff; }
  .btn-reset { background:#dc2626; color:#fff; }

  table { width:100%; max-width:700px; margin:0 auto 20px; border-collapse:collapse; background:#0d0d2b; border-radius:10px; overflow:hidden; }
  th, td { padding:12px; text-align:center; border-bottom:1px solid #1a3a8a; }
  th { background:#0a0a2e; color:#3b82f6; }
  td { color:#e2e8f0; }
  .back { display:block; text-align:center; color:#3b82f6; text-decoration:none; margin-top:20px; }
  .back:hover { color:#60a5fa; }
  .asistencia-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:10px; max-width:1100px; margin:0 auto 15px; }
  .asist-item { display:flex; align-items:center; justify-content:space-between; gap:8px; background:#0d0d2b; border-radius:10px; padding:8px 12px; border:1px solid #1a3a8a; flex-wrap:wrap; }
  .asist-item .name { font-weight:bold; color:#e2e8f0; font-size:0.9em; min-width:120px; }
  .asist-item .btns { display:flex; gap:4px; flex-wrap:wrap; }
  .asist-item .btns button { padding:4px 10px; border-radius:6px; border:2px solid #1a3a8a; background:#0a0a0a; color:#4a6a8a; cursor:pointer; font-size:0.75em; font-weight:bold; transition:.2s; }
  .asist-item .btns button.on { border-color:#3b82f6; background:rgba(59,130,246,0.15); color:#3b82f6; }
  .asist-item .btns button.on.sede { border-color:#3b82f6; background:rgba(59,130,246,0.15); color:#3b82f6; }
  .asist-item .btns button.on.movil { border-color:#f59e0b; background:rgba(245,158,11,0.15); color:#f59e0b; }
  .asist-item .btns button.on.mision { border-color:#8b5cf6; background:rgba(139,92,246,0.15); color:#8b5cf6; }
  .asist-item .btns button.on.ausente { border-color:#ef4444; background:rgba(239,68,68,0.15); color:#ef4444; }
  .asist-item .btns button.on.incapacidad { border-color:#f97316; background:rgba(249,115,22,0.15); color:#f97316; }
  .asist-item .btns button.on.consulta { border-color:#14b8a6; background:rgba(20,184,166,0.15); color:#14b8a6; }
  .asist-btn { margin:0 auto 15px; display:block; padding:10px 25px; background:#2563eb; color:#fff; border:none; border-radius:10px; font-size:1em; font-weight:bold; cursor:pointer; }
  .asist-btn:hover { background:#1d4ed8; }
  .btn-report { background:#6366f1; color:#fff; }
  #reporteSemanal { display:none; max-width:900px; margin:15px auto; background:#0d0d2b; border-radius:12px; padding:20px; overflow-x:auto; border:1px solid #1a3a8a; }
  @media print {
    .nav-grid, .grid, .actions, .asistencia-grid, .asist-btn, .back { display:none; }
    table { box-shadow:none; }
  }
</style>
</head>
<body>
  <div class="top">
    <img class="logo" src="data:image/png;base64,__LOGO2__" alt="Logo">
    <h1>Sistema de Turnos</h1>
    <div class="user">Usuario: __USER__</div>
  </div>
  <div class="nav-grid">
    <a class="nav-card pub" href="/" target="_blank">
      <div class="icon">🖥️</div>
      <div class="tit">Pantalla Pública</div>
    </a>
    <a class="nav-card tec" href="/tecnico" target="_blank">
      <div class="icon">🔧</div>
      <div class="tit">Panel Técnicos</div>
    </a>
  </div>

  <div class="section-title">Control de Técnicos</div>
  <div class="grid" id="grid"></div>

  <div class="actions">
    <button class="btn-print" onclick="window.print()">🖨️ Imprimir informe del día</button>
    <button class="btn-report" onclick="generarInforme()">📊 Informe semanal</button>
    <button class="btn-reset" onclick="resetSistema()">🗑️ Reiniciar sistema</button>
  </div>

  <div id="reporteSemanal"></div>

  <div class="section-title">Asistencia del Día</div>
  <div class="asistencia-grid" id="asistGrid"></div>
  <button class="asist-btn" onclick="guardarAsistencia()">💾 Guardar Asistencia</button>

  <table id="report">
    <thead><tr><th>Técnico</th><th>Estado</th><th>Asistencia</th><th>Espera / Atendidos</th></tr></thead>
    <tbody id="reportBody"></tbody>
    <tfoot><tr><th>Total</th><th></th><th></th><th id="totalAtt">0</th></tr></tfoot>
  </table>

  <a href="/" class="back">← Pantalla pública</a> | <a href="/logout" class="back">Cerrar sesión</a>

<script>
  const techNames = ['Mauricio Amaya', 'Julio Castillo', 'Jorge Hernandez', 'Yesica Bonilla', 'Alba Zelaya', 'Manuel Herrera', 'William Espiñal', 'Rene Quintanilla'];
  const asistOpts = [
    {key:'sede', lbl:'🏢 Sede', cls:'sede'},
    {key:'movil', lbl:'🚐 Móvil', cls:'movil'},
    {key:'mision', lbl:'🏛️ Misión Oficial', cls:'mision'},
    {key:'ausente', lbl:'❌ Ausente', cls:'ausente'},
    {key:'incapacidad', lbl:'🏥 Incapacidad', cls:'incapacidad'},
    {key:'consulta', lbl:'📋 Consulta', cls:'consulta'}
  ];
  let asistencia = {};

  function initAsistencia() {
    fetch('/api/estado').then(r=>r.json()).then(data => {
      const saved = data.attendance_today || {};
      asistencia = {};
      for (let i = 0; i < 8; i++) asistencia[i] = saved[i] || 'sede';
      renderAsistencia();
    });
  }
  function renderAsistencia() {
    const grid = document.getElementById('asistGrid'); if (!grid) return;
    grid.innerHTML = '';
    for (let i = 0; i < 8; i++) {
      const val = asistencia[i] || 'sede';
      const div = document.createElement('div');
      div.className = 'asist-item';
      const name = document.createElement('span');
      name.className = 'name';
      name.textContent = techNames[i];
      div.appendChild(name);
      const btns = document.createElement('div');
      btns.className = 'btns';
      asistOpts.forEach(o => {
        const btn = document.createElement('button');
        btn.className = val === o.key ? 'on ' + o.cls : '';
        btn.textContent = o.lbl;
        btn.onclick = function() { toggleAsist(i, o.key); };
        btns.appendChild(btn);
      });
      div.appendChild(btns);
      grid.appendChild(div);
    }
  }
  function toggleAsist(i, tipo) {
    asistencia[i] = tipo;
    renderAsistencia();
  }
  function guardarAsistencia() {
    fetch('/api/asistencia', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({registro: asistencia})})
      .then(r=>r.json()).then(d=>{
        if(d.success) alert('Asistencia guardada');
        else alert('Error: ' + (d.error || 'desconocido'));
      }).catch(e => alert('Error de red: ' + e.message));
  }
  function generarInforme() {
    fetch('/api/informe_semanal').then(r=>r.json()).then(data => {
      const dias = Object.keys(data).sort();
      const opts = {sede:'🏢 Sede', movil:'🚐 Móvil', mision:'🏛️ M.Oficial', ausente:'❌ Ausente', incapacidad:'🏥 Incapacidad', consulta:'📋 Consulta'};
      let html = '<table style="width:100%;border-collapse:collapse;font-size:0.85em;"><thead><tr><th>Técnico</th>';
      dias.forEach(d => {
        const parts = d.split('-');
        html += '<th>' + parts[2] + '/' + parts[1] + '</th>';
      });
      html += '</tr></thead><tbody>';
      for (let i = 0; i < 8; i++) {
        html += '<tr><td style="font-weight:bold;padding:6px 8px;border-bottom:1px solid #1a3a8a;color:#e2e8f0;">' + techNames[i] + '</td>';
        dias.forEach(d => {
          const v = (data[d] || {})[i] || '—';
          html += '<td style="padding:6px 8px;text-align:center;border-bottom:1px solid #1a3a8a;color:#e2e8f0;white-space:nowrap;">' + (opts[v] || '—') + '</td>';
        });
        html += '</tr>';
      }
      html += '</tbody></table>';
      const el = document.getElementById('reporteSemanal');
      el.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;"><h3 style="margin:0;color:#3b82f6;">📊 Informe Semanal de Asistencia</h3><button onclick="this.parentElement.parentElement.style.display=\\'none\\'" style="background:#ef4444;color:#fff;border:none;border-radius:8px;padding:6px 14px;cursor:pointer;">Cerrar</button></div>' + html;
      el.style.display = 'block';
    });
  }
  function render(data) {
    const grid = document.getElementById('grid'); grid.innerHTML = '';
    for (let i = 0; i < 8; i++) {
      const pend = data.pending[i]; const on = data.active[i];
      const first = pend.length > 0 ? pend[0] : null;
      const div = document.createElement('div');
      div.className = 'card' + (on ? '' : ' off');
      div.innerHTML =
        '<div class="vnum">' + techNames[i] + '</div>' +
        '<div class="current ' + (first ? '' : 'none') + '">' + (first ? first : '---') + '</div>' +
        '<div class="pend">En espera: ' + pend.length + '</div>' +
        '<div class="att">Atendidos: ' + (data.attended[i] || []).length + '</div>' +
        '<button class="btn ' + (on ? '' : 'btn-off') + '" onclick="toggle(' + (i+1) + ')">' + (on ? '🟢 Activo' : '⚪ Inactivo') + '</button>';
      grid.appendChild(div);
    }
    const rb = document.getElementById('reportBody'); rb.innerHTML = '';
    let total = 0;
    for (let i = 0; i < 8; i++) {
      total += (data.attended[i] || []).length;
      const tr = document.createElement('tr');
      const asLabels = {sede:'🏢 Sede', movil:'🚐 Móvil', mision:'🏛️ Misión Oficial', ausente:'❌ Ausente', incapacidad:'🏥 Incapacidad', consulta:'📋 Consulta'};
      const asVal = (data.attendance_today || {})[i] || '—';
      const asIcon = asLabels[asVal] || '—';
      tr.innerHTML = '<td>' + techNames[i] + '</td><td>' + (data.active[i] ? '🟢 Activo' : '⚪ Inactivo') + '</td><td>' + asIcon + '</td><td>Espera: ' + data.pending[i].length + ' / Atend: ' + (data.attended[i] || []).length + '</td>';
      rb.appendChild(tr);
    }
    document.getElementById('totalAtt').textContent = total;
  }
  function toggle(v) { fetch('/api/toggle_tecnico/' + v, {method:'POST'}).then(()=>actualizar()); }
  function resetSistema() { if (confirm('¿Reiniciar todo el sistema?')) fetch('/api/reset', {method:'POST'}).then(()=>actualizar()); }
  function actualizar() { fetch('/api/estado').then(r=>r.json()).then(render).catch(e => console.error('Error polling:', e)); }
  initAsistencia(); actualizar(); setInterval(actualizar, 1500);
</script>
</body>
</html>
"""

# ─── RUTAS ──────────────────────────────────────────────────────
@app.route("/")
def display():
    return DISPLAY_PAGE.replace("__LOGO1__", LOGO1_B64)

@app.route("/central", methods=["GET", "POST"])
def central():
    login = LOGIN_PAGE.replace("__LOGO2__", LOGO2_B64)
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        if user in admins:
            session["user"] = user
            return redirect("/central")
        else:
            return render_template_string(login, error="Usuario no autorizado")
    if "user" not in session:
        return render_template_string(login, error=None)
    return CENTRAL_PAGE.replace("__USER__", session["user"]).replace("__LOGO2__", LOGO2_B64)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/central")

@app.route("/logout-tecnico")
def logout_tecnico():
    session.pop("tecnico", None)
    return redirect("/tecnico")

@app.route("/tecnico", methods=["GET", "POST"])
def tech_login():
    if request.method == "POST":
        user = request.form.get("username", "").strip().lower()
        matched = None
        for i, name in enumerate(techNames):
            if name.lower() == user:
                matched = i + 1
                break
        if matched:
            session["tecnico"] = matched
            return redirect("/tecnico/" + str(matched))
        else:
            return render_template_string(TECH_LOGIN.replace("__LOGO3__", LOGO3_B64), error="Nombre no encontrado")
    if "tecnico" in session:
        return redirect("/tecnico/" + str(session["tecnico"]))
    return render_template_string(TECH_LOGIN.replace("__LOGO3__", LOGO3_B64), error=None)

@app.route("/tecnico/<int:v>")
def tech_view(v):
    if "tecnico" not in session:
        return redirect("/tecnico")
    if session["tecnico"] != v:
        return redirect("/tecnico/" + str(session["tecnico"]))
    if not 1 <= v <= 8:
        return redirect("/tecnico")
    name = techNames[v-1]
    return TECH_PAGE.replace("__V__", str(v)).replace("__NAME__", name)

@app.route("/api/tomar_turno", methods=["POST"])
def tomar_turno():
    with lock:
        num = state["next"]
        state["next"] += 1
        candidates = [(i, len(state["pending"][i])) for i in range(8) if state["active"][i]]
        if not candidates:
            return jsonify({"success": False, "error": "No hay tecnicos activos"})
        ventanilla = min(candidates, key=lambda x: x[1])[0]
        state["pending"][ventanilla].append(num)
        broadcast({"type": "nuevo", "num": num, "ventanilla": ventanilla + 1, "ts": time.time()})
    return jsonify({"success": True, "num": num, "ventanilla": ventanilla + 1})

@app.route("/api/atender_siguiente/<int:ventanilla>", methods=["POST"])
def atender_siguiente(ventanilla):
    if not 1 <= ventanilla <= 8:
        return jsonify({"success": False, "error": "Tecnico invalido"})
    with lock:
        check_day()
        if not state["active"][ventanilla - 1]:
            return jsonify({"success": False, "error": "Tecnico inactivo"})
        if not state["pending"][ventanilla - 1]:
            return jsonify({"success": False, "error": "No hay turnos en espera"})
        num = state["pending"][ventanilla - 1].pop(0)
        state["attended"][ventanilla - 1].append(num)
        broadcast({"type": "llamada", "num": num, "ventanilla": ventanilla, "ts": time.time()})
    return jsonify({"success": True, "num": num, "ventanilla": ventanilla})

@app.route("/api/toggle_tecnico/<int:ventanilla>", methods=["POST"])
def toggle_tecnico(ventanilla):
    if not 1 <= ventanilla <= 8:
        return jsonify({"success": False, "error": "Tecnico invalido"})
    with lock:
        state["active"][ventanilla - 1] = not state["active"][ventanilla - 1]
        if not state["active"][ventanilla - 1]:
            state["pending"][ventanilla - 1] = []
    return jsonify({"success": True, "active": state["active"][ventanilla - 1]})

@app.route("/api/estado")
def estado():
    with lock:
        return jsonify({
            "next": state["next"],
            "pending": [list(q) for q in state["pending"]],
            "active": list(state["active"]),
            "attended": list(state["attended"]),
            "last_event": state["last_event"],
            "attendance_today": state["attendance"].get(str(date.today()), {})
        })

@app.route("/api/asistencia", methods=["POST"])
def guardar_asistencia():
    data = request.get_json()
    if not data or "registro" not in data:
        return jsonify({"success": False, "error": "Datos invalidos"})
    with lock:
        hoy = str(date.today())
        current = state["attendance"].get(hoy, {})
        current.update(data["registro"])
        state["attendance"][hoy] = current
    return jsonify({"success": True})

@app.route("/api/informe_semanal")
def informe_semanal():
    from datetime import timedelta
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    with lock:
        report = {}
        for i in range(7):
            d = str(lunes + timedelta(days=i))
            report[d] = state["attendance"].get(d, {})
    return jsonify(report)

@app.route("/api/reset", methods=["POST"])
def reset():
    with lock:
        state["next"] = 1
        state["pending"] = [[] for _ in range(8)]
        state["active"] = [True] * 8
        state["attended"] = [[] for _ in range(8)]
        state["last_event"] = None
    return jsonify({"success": True})

if __name__ == "__main__":
    print("=" * 50)
    print("  SISTEMA DE TURNOS")
    print("  Central:   http://localhost:5000/central")
    print("  Pantalla:  http://localhost:5000")
    print("  Tecnico:   http://localhost:5000/tecnico")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
