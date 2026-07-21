# -*- coding: utf-8 -*-
"""
Sistema de Turnos de Espera
8 tecnicos, reasignacion, activar/desactivar, voz en espanol.
Tecnico ve solo su ventanilla. Admin imprime informe diario.
"""

import threading
import time
from datetime import date
from flask import Flask, render_template_string, request, jsonify, redirect

app = Flask(__name__)

lock = threading.Lock()
state = {
    "next": 1,
    "pending": [[] for _ in range(8)],
    "active": [True] * 8,
    "attended": [0] * 8,
    "day": str(date.today()),
    "last_event": None,
}

def broadcast(event):
    state["last_event"] = event

def check_day():
    hoy = str(date.today())
    if state["day"] != hoy:
        state["day"] = hoy
        state["pending"] = [[] for _ in range(8)]
        state["attended"] = [0] * 8

# ─── PANTALLA PUBLICA ───────────────────────────────────────────
DISPLAY_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Turnos en Espera</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',sans-serif; background:#0f172a; color:#fff; min-height:100vh; }
  .top { background:#1e293b; padding:15px 30px; display:flex; justify-content:space-between; align-items:center; }
  .top h1 { font-size:1.4em; color:#38bdf8; }
  .waiting { background:#334155; padding:10px 30px; text-align:center; font-size:1.4em; }
  .waiting b { color:#fbbf24; font-size:1.6em; }
  .anuncio { text-align:center; padding:30px 20px; background:linear-gradient(135deg,#022c22,#065f46); min-height:42vh; display:flex; flex-direction:column; justify-content:center; }
  .anuncio .msg { font-size:clamp(2.5em,7vw,5em); font-weight:bold; color:#fff; line-height:1.1; }
  .anuncio .num { font-size:clamp(10em,35vw,28em); font-weight:900; color:#fbbf24; line-height:0.85; text-shadow:0 0 60px rgba(251,191,36,.6); }
  .anuncio .sub { font-size:clamp(2em,5vw,4em); color:#a7f3d0; margin-top:15px; }
  .anuncio.idle .num { color:#475569; font-size:clamp(3em,10vw,7em); }
  .anuncio.idle .msg, .anuncio.idle .sub { color:#64748b; }
  .grid { display:grid; grid-template-columns:repeat(4,1fr); gap:20px; padding:30px; }
  .win { background:#1e293b; border-radius:20px; padding:20px; text-align:center; border:3px solid #334155; min-height:170px; display:flex; flex-direction:column; justify-content:center; }
  .win.active { border-color:#22c55e; }
  .win.off { opacity:0.35; }
  .win .num { font-size:2.5em; font-weight:bold; color:#fbbf24; }
  .win .lbl { font-size:0.9em; color:#94a3b8; margin-top:6px; }
  .win .empty { color:#64748b; font-size:2em; }
  .win .count { font-size:0.85em; color:#38bdf8; margin-top:4px; }
  .btn-turno { display:block; width:320px; margin:0 auto 20px; padding:18px; background:#38bdf8; color:#0f172a; border:none; border-radius:15px; font-size:1.4em; font-weight:bold; cursor:pointer; }
  .btn-turno:hover { background:#0ea5e9; }
  @media(max-width:900px){ .grid{grid-template-columns:repeat(2,1fr);} }
</style>
</head>
<body>
  <div class="top">
    <h1>🏥 Sistema de Turnos</h1>
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
  const techNames = ['Mauricio Amaya', 'Julio Castillo', 'Jorge Hernandez', 'Yesica Bonilla', 'Alba Zelaya', 'Manuel Herrera', 'Pendiente 7', 'Pendiente 8'];
  let ultimoTs = null;
  function tomarTurno() {
    fetch('/api/tomar_turno', {method:'POST'}).then(r=>r.json()).then(d=>{
      if (d.success) {
        document.getElementById('anuncio').className = 'anuncio';
        document.getElementById('anum').textContent = d.num;
        document.getElementById('asub').textContent = techNames[d.ventanilla-1];
        document.querySelector('#anuncio .msg').textContent = 'Su turno es:';
      }
    });
  }
  function hablar(num, tec) {
    if ('speechSynthesis' in window) {
      const u = new SpeechSynthesisUtterance('Usted pasara con ' + tec + ', con el numero ' + num);
      u.lang = 'es-ES'; u.rate = 0.9;
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
      if (pend.length > 0) {
        div.innerHTML = '<div class="num">' + pend[0] + '</div><div class="lbl">' + techNames[i] + (on ? '' : ' (off)') + '</div><div class="count">Esperando: ' + pend.length + '</div>';
      } else {
        div.innerHTML = '<div class="empty">---</div><div class="lbl">' + techNames[i] + (on ? '' : ' (off)') + '</div>';
      }
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
        document.getElementById('asub').textContent = techNames[ev.ventanilla-1];
        document.querySelector('#anuncio .msg').textContent = 'Turno asignado';
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

# ─── SELECCION DE TECNICO ──────────────────────────────────────
techNames = ['Mauricio Amaya', 'Julio Castillo', 'Jorge Hernandez', 'Yesica Bonilla', 'Alba Zelaya', 'Manuel Herrera', 'Pendiente 7', 'Pendiente 8']

TECH_SELECT = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Panel Tecnico</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',sans-serif; background:#0f172a; color:#fff; min-height:100vh; padding:30px; }
  h1 { text-align:center; color:#38bdf8; margin-bottom:30px; }
  .grid { display:grid; grid-template-columns:repeat(4,1fr); gap:20px; max-width:900px; margin:0 auto; }
  .btn { padding:40px; background:#1e293b; color:#fff; border:3px solid #334155; border-radius:20px; font-size:1.5em; font-weight:bold; cursor:pointer; transition:.3s; }
  .btn:hover { border-color:#22c55e; background:#065f46; transform:scale(1.05); }
  .back { display:block; text-align:center; margin-top:30px; color:#64748b; text-decoration:none; }
</style>
</head>
<body>
  <h1>🔧 Seleccione su ventanilla</h1>
  <div class="grid">
    {% for i in range(0,8) %}<button class="btn" onclick="location.href='/tecnico/{{ i+1 }}'">{{ names[i] }}</button>{% endfor %}
  </div>
  <a href="/" class="back">← Pantalla pública</a>
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
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',sans-serif; background:#f1f5f9; min-height:100vh; padding:20px; }
  .card { max-width:500px; margin:30px auto; background:#fff; border-radius:20px; padding:30px; text-align:center; box-shadow:0 5px 20px rgba(0,0,0,.1); }
  .vnum { color:#64748b; font-size:1.2em; font-weight:bold; }
  .pend-list { text-align:left; margin:15px 0; max-height:250px; overflow-y:auto; }
  .pend-item { display:flex; justify-content:space-between; align-items:center; padding:10px 15px; background:#f8fafc; border-radius:10px; margin-bottom:6px; border:1px solid #e2e8f0; }
  .pend-item .n { font-size:1.5em; font-weight:bold; color:#0ea5e9; }
  .pend-item .p { color:#64748b; font-size:0.85em; }
  .empty-pend { color:#94a3b8; text-align:center; padding:20px; font-size:1.1em; }
  .count { background:#e0f2fe; color:#0369a1; padding:10px; border-radius:12px; font-size:1.1em; margin:10px 0; }
  .btn { width:100%; padding:18px; background:#22c55e; color:#fff; border:none; border-radius:12px; font-size:1.3em; font-weight:bold; cursor:pointer; margin-top:10px; }
  .btn:hover { background:#16a34a; }
  .btn:disabled { background:#cbd5e1; cursor:not-allowed; }
  .btn-off { background:#94a3b8; }
  .back { display:block; text-align:center; margin-top:15px; color:#0ea5e9; text-decoration:none; }
  .off-msg { color:#ef4444; font-weight:bold; margin:15px 0; }
</style>
</head>
<body>
  <div class="card" id="card">
    <div class="vnum">__NAME__</div>
    <div class="count" id="count">Esperando: 0</div>
    <div class="pend-list" id="pendList"><div class="empty-pend">Sin turnos en espera</div></div>
    <div id="offmsg"></div>
    <button class="btn" id="btnAtender" onclick="atender()">📢 Atender siguiente</button>
  </div>
  <a href="/tecnico" class="back">← Cambiar ventanilla</a>
  <a href="/" class="back">← Pantalla pública</a>

<script>
  const v = __V__;
  function render(data) {
    const pend = data.pending[v-1]; const on = data.active[v-1];
    document.getElementById('count').textContent = 'Esperando: ' + pend.length;
    const list = document.getElementById('pendList');
    list.innerHTML = '';
    if (pend.length === 0) {
      list.innerHTML = '<div class="empty-pend">Sin turnos en espera</div>';
    } else {
      pend.forEach((n, idx) => {
        const item = document.createElement('div');
        item.className = 'pend-item';
        item.innerHTML = '<span class="p">#' + (idx+1) + '</span><span class="n">' + n + '</span>';
        list.appendChild(item);
      });
    }
    const btn = document.getElementById('btnAtender');
    const off = document.getElementById('offmsg');
    if (!on) {
      btn.disabled = true; btn.textContent = '⚪ Inactivo';
      btn.className = 'btn btn-off';
      off.innerHTML = '<div class="off-msg">Técnico inactivo. Pida al administrador que lo active.</div>';
    } else {
      btn.disabled = (pend.length === 0);
      btn.textContent = '📢 Atender siguiente';
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
  actualizar(); setInterval(actualizar, 1500);
</script>
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
  body { font-family:'Segoe UI',sans-serif; background:#f1f5f9; min-height:100vh; padding:20px; }
  .top { text-align:center; margin-bottom:15px; }
  h1 { color:#0f172a; }
  .nav-grid { display:flex; justify-content:center; gap:12px; margin:0 auto 25px; max-width:650px; }
  .nav-card { width:240px; background:#1e293b; border-radius:15px; padding:20px; text-align:center; text-decoration:none; color:#fff; border:2px solid #334155; transition:.3s; cursor:pointer; display:block; }
  .nav-card:hover { transform:scale(1.04); }
  .nav-card.pub:hover { border-color:#22c55e; background:#065f46; }
  .nav-card.tec:hover { border-color:#38bdf8; background:#0c4a6e; }
  .nav-card.adm { border-color:#fbbf24; background:#1e293b; }
  .nav-card .icon { font-size:2em; margin-bottom:5px; }
  .nav-card .tit { font-size:1.1em; font-weight:bold; }
  .section-title { text-align:center; font-size:1.2em; color:#0f172a; margin:20px 0 10px; font-weight:bold; border-top:2px solid #e2e8f0; padding-top:20px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:15px; max-width:1100px; margin:0 auto 20px; }
  .card { background:#fff; border-radius:15px; padding:20px; text-align:center; box-shadow:0 3px 10px rgba(0,0,0,.1); border:2px solid #e2e8f0; }
  .card.off { opacity:0.5; }
  .card .vnum { font-size:1em; color:#64748b; }
  .card .current { font-size:2.5em; font-weight:bold; color:#0ea5e9; margin:8px 0; }
  .card .current.none { color:#cbd5e1; }
  .card .pend { color:#f59e0b; font-weight:bold; font-size:0.9em; }
  .card .att { color:#16a34a; font-weight:bold; }
  .btn { width:100%; padding:10px; background:#22c55e; color:#fff; border:none; border-radius:10px; font-size:1em; cursor:pointer; margin-top:6px; }
  .btn-off { background:#94a3b8; }
  .actions { text-align:center; margin-bottom:20px; }
  .actions button { padding:10px 20px; margin:0 5px; border:none; border-radius:10px; cursor:pointer; font-weight:bold; }
  .btn-print { background:#0ea5e9; color:#fff; }
  .btn-reset { background:#ef4444; color:#fff; }
  table { width:100%; max-width:700px; margin:0 auto 20px; border-collapse:collapse; background:#fff; border-radius:10px; overflow:hidden; }
  th, td { padding:12px; text-align:center; border-bottom:1px solid #eee; }
  th { background:#1e293b; color:#fff; }
  .back { display:block; text-align:center; color:#0ea5e9; text-decoration:none; margin-top:20px; }
  @media print {
    .nav-grid, .grid, .actions, .back { display:none; }
    table { box-shadow:none; }
  }
</style>
</head>
<body>
  <div class="top"><h1>🏥 Sistema de Turnos</h1></div>
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
    <button class="btn-reset" onclick="resetSistema()">🗑️ Reiniciar sistema</button>
  </div>

  <table id="report">
    <thead><tr><th>Técnico</th><th>Estado</th><th>Espera / Atendidos</th></tr></thead>
    <tbody id="reportBody"></tbody>
    <tfoot><tr><th>Total</th><th></th><th id="totalAtt">0</th></tr></tfoot>
  </table>

  <a href="/" class="back">← Pantalla pública</a>

<script>
  const techNames = ['Mauricio Amaya', 'Julio Castillo', 'Jorge Hernandez', 'Yesica Bonilla', 'Alba Zelaya', 'Manuel Herrera', 'Pendiente 7', 'Pendiente 8'];
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
        '<div class="att">Atendidos: ' + data.attended[i] + '</div>' +
        '<button class="btn ' + (on ? '' : 'btn-off') + '" onclick="toggle(' + (i+1) + ')">' + (on ? '🟢 Activo' : '⚪ Inactivo') + '</button>';
      grid.appendChild(div);
    }
    const rb = document.getElementById('reportBody'); rb.innerHTML = '';
    let total = 0;
    for (let i = 0; i < 8; i++) {
      total += data.attended[i];
      const tr = document.createElement('tr');
      tr.innerHTML = '<td>' + techNames[i] + '</td><td>' + (data.active[i] ? '🟢 Activo' : '⚪ Inactivo') + '</td><td>Espera: ' + data.pending[i].length + ' / Atend: ' + data.attended[i] + '</td>';
      rb.appendChild(tr);
    }
    document.getElementById('totalAtt').textContent = total;
  }
  function toggle(v) { fetch('/api/toggle_tecnico/' + v, {method:'POST'}).then(()=>actualizar()); }
  function resetSistema() { if (confirm('¿Reiniciar todo el sistema?')) fetch('/api/reset', {method:'POST'}).then(()=>actualizar()); }
  function actualizar() { fetch('/api/estado').then(r=>r.json()).then(render); }
  actualizar(); setInterval(actualizar, 1500);
</script>
</body>
</html>
"""

# ─── RUTAS ──────────────────────────────────────────────────────
@app.route("/")
def display():
    return DISPLAY_PAGE

@app.route("/central")
def central():
    return CENTRAL_PAGE

@app.route("/tecnico")
def tech_select():
    return render_template_string(TECH_SELECT, names=techNames)

@app.route("/tecnico/<int:v>")
def tech_view(v):
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
        state["attended"][ventanilla - 1] += 1
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
            "last_event": state["last_event"]
        })

@app.route("/api/reset", methods=["POST"])
def reset():
    with lock:
        state["next"] = 1
        state["pending"] = [[] for _ in range(8)]
        state["active"] = [True] * 8
        state["attended"] = [0] * 8
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
