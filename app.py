# -*- coding: utf-8 -*-
"""
Sistema de Turnos de Espera
8 tecnicos, reasignacion, activar/desactivar, voz en espanol.
"""

import threading
import time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

lock = threading.Lock()
state = {
    "next": 1,
    "queue": [],
    "windows": [None] * 8,
    "active": [True] * 8,
    "last_event": None,
}

def broadcast(event):
    state["last_event"] = event

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

  /* ANUNCIO GRANDE */
  .anuncio { text-align:center; padding:30px 20px; background:linear-gradient(135deg,#022c22,#065f46); min-height:42vh; display:flex; flex-direction:column; justify-content:center; }
  .anuncio .msg { font-size:clamp(2em,6vw,4.5em); font-weight:bold; color:#fff; line-height:1.1; }
  .anuncio .num { font-size:clamp(8em,30vw,22em); font-weight:900; color:#fbbf24; line-height:0.9; text-shadow:0 0 40px rgba(251,191,36,.5); }
  .anuncio .sub { font-size:clamp(1.5em,4vw,3em); color:#a7f3d0; margin-top:10px; }
  .anuncio.idle .num { color:#475569; font-size:clamp(3em,10vw,7em); }
  .anuncio.idle .msg, .anuncio.idle .sub { color:#64748b; }

  .grid { display:grid; grid-template-columns:repeat(4,1fr); gap:20px; padding:30px; }
  .win { background:#1e293b; border-radius:20px; padding:25px; text-align:center; border:3px solid #334155; min-height:150px; }
  .win.active { border-color:#22c55e; }
  .win.off { opacity:0.35; }
  .win .num { font-size:3em; font-weight:bold; color:#fbbf24; }
  .win .lbl { font-size:1em; color:#94a3b8; margin-top:10px; }
  .win .empty { color:#64748b; font-size:2em; }
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
  let ultimoTs = null;

  function tomarTurno() {
    fetch('/api/tomar_turno', {method:'POST'}).then(r=>r.json()).then(d=>{
      if (d.success) alert('Su turno es: ' + d.num + '\\nEspere a ser llamado.');
    });
  }

  function hablar(num, tec) {
    if ('speechSynthesis' in window) {
      const txt = 'Usted pasara con el tecnico ' + tec + ', con el numero ' + num;
      const u = new SpeechSynthesisUtterance(txt);
      u.lang = 'es-ES';
      u.rate = 0.9;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    }
  }

  function render(data) {
    document.getElementById('waitingCount').textContent = data.queue.length;
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    for (let i = 0; i < 8; i++) {
      const t = data.windows[i];
      const on = data.active[i];
      const div = document.createElement('div');
      div.className = 'win ' + (on ? 'active' : 'off');
      if (t) {
        div.innerHTML = '<div class="num">' + t + '</div><div class="lbl">Tecnico ' + (i+1) + (on ? '' : ' (off)') + '</div>';
      } else {
        div.innerHTML = '<div class="empty">---</div><div class="lbl">Tecnico ' + (i+1) + (on ? '' : ' (off)') + '</div>';
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
        const a = document.getElementById('anuncio');
        a.className = 'anuncio';
        document.getElementById('anum').textContent = ev.num;
        document.getElementById('asub').textContent = 'Usted pasara con el tecnico ' + ev.ventanilla;
        document.querySelector('#anuncio .msg').textContent = 'Turno asignado';
        hablar(ev.num, ev.ventanilla);
      }
    });
  }

  setInterval(()=>{ document.getElementById('clock').textContent = new Date().toLocaleTimeString('es-ES'); }, 1000);
  actualizar();
  setInterval(actualizar, 1000);
</script>
</body>
</html>
"""

# ─── PANEL DEL TECNICO ──────────────────────────────────────────
TECH_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Panel Tecnico - Turnos</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',sans-serif; background:#f1f5f9; min-height:100vh; padding:20px; }
  .top { text-align:center; margin-bottom:15px; }
  .top h1 { color:#0f172a; }
  .waiting { text-align:center; margin-bottom:15px; color:#475569; font-size:1.1em; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:15px; max-width:1100px; margin:0 auto; }
  .card { background:#fff; border-radius:15px; padding:20px; text-align:center; box-shadow:0 3px 10px rgba(0,0,0,.1); border:2px solid #e2e8f0; }
  .card.off { opacity:0.5; }
  .card .vnum { font-size:1em; color:#64748b; }
  .card .current { font-size:3em; font-weight:bold; color:#0ea5e9; margin:10px 0; }
  .card .current.none { color:#cbd5e1; }
  .btn { width:100%; padding:12px; background:#22c55e; color:#fff; border:none; border-radius:10px; font-size:1em; font-weight:bold; cursor:pointer; margin-top:8px; }
  .btn:hover { background:#16a34a; }
  .btn:disabled { background:#cbd5e1; cursor:not-allowed; }
  .btn-off { background:#94a3b8; }
  .btn-off:hover { background:#64748b; }
  .reset { display:block; margin:20px auto; padding:10px 25px; background:#ef4444; color:#fff; border:none; border-radius:10px; cursor:pointer; }
  .back { display:block; text-align:center; margin-top:15px; color:#0ea5e9; text-decoration:none; }
</style>
</head>
<body>
  <div class="top">
    <h1>🔧 Panel del Tecnico</h1>
    <div class="waiting">En espera: <b id="wc">0</b></div>
  </div>
  <div class="grid" id="grid"></div>
  <button class="reset" onclick="resetSistema()">🗑️ Reiniciar sistema</button>
  <a href="/" class="back">← Pantalla publica</a>

<script>
  function render(data) {
    document.getElementById('wc').textContent = data.queue.length;
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    for (let i = 0; i < 8; i++) {
      const t = data.windows[i];
      const on = data.active[i];
      const div = document.createElement('div');
      div.className = 'card' + (on ? '' : ' off');
      div.innerHTML =
        '<div class="vnum">Tecnico ' + (i+1) + '</div>' +
        '<div class="current ' + (t ? '' : 'none') + '">' + (t ? t : '---') + '</div>' +
        '<button class="btn ' + (on ? '' : 'btn-off') + '" onclick="toggle(' + (i+1) + ')">' + (on ? '🟢 Activo' : '⚪ Inactivo') + '</button>' +
        '<button class="btn" onclick="llamar(' + (i+1) + ')" ' + ((!on || data.queue.length===0) ? 'disabled' : '') + '>📢 Llamar siguiente</button>';
      grid.appendChild(div);
    }
  }

  function llamar(v) {
    fetch('/api/llamar_siguiente/' + v, {method:'POST'}).then(r=>r.json()).then(d=>{
      if (!d.success && d.error) alert(d.error);
      actualizar();
    });
  }

  function toggle(v) {
    fetch('/api/toggle_tecnico/' + v, {method:'POST'}).then(()=>actualizar());
  }

  function resetSistema() {
    if (confirm('¿Reiniciar todo el sistema?')) {
      fetch('/api/reset', {method:'POST'}).then(()=>actualizar());
    }
  }

  function actualizar() {
    fetch('/api/estado').then(r=>r.json()).then(render);
  }

  actualizar();
  setInterval(actualizar, 1500);
</script>
</body>
</html>
"""

# ─── RUTAS ──────────────────────────────────────────────────────
@app.route("/")
def display():
    return DISPLAY_PAGE

@app.route("/tecnico")
def tech():
    return TECH_PAGE

@app.route("/api/tomar_turno", methods=["POST"])
def tomar_turno():
    with lock:
        num = state["next"]
        state["next"] += 1
        state["queue"].append(num)
        broadcast({"type": "nuevo", "num": num, "ventanilla": None, "ts": time.time()})
    return jsonify({"success": True, "num": num})

@app.route("/api/llamar_siguiente/<int:ventanilla>", methods=["POST"])
def llamar_siguiente(ventanilla):
    if not 1 <= ventanilla <= 8:
        return jsonify({"success": False, "error": "Tecnico invalido"})
    with lock:
        if not state["active"][ventanilla - 1]:
            return jsonify({"success": False, "error": "Tecnico inactivo"})
        if not state["queue"]:
            return jsonify({"success": False, "error": "No hay turnos en espera"})
        num = state["queue"].pop(0)
        state["windows"][ventanilla - 1] = num
        broadcast({"type": "llamada", "num": num, "ventanilla": ventanilla, "ts": time.time()})
    return jsonify({"success": True, "num": num, "ventanilla": ventanilla})

@app.route("/api/toggle_tecnico/<int:ventanilla>", methods=["POST"])
def toggle_tecnico(ventanilla):
    if not 1 <= ventanilla <= 8:
        return jsonify({"success": False, "error": "Tecnico invalido"})
    with lock:
        state["active"][ventanilla - 1] = not state["active"][ventanilla - 1]
        if not state["active"][ventanilla - 1]:
            state["windows"][ventanilla - 1] = None
    return jsonify({"success": True, "active": state["active"][ventanilla - 1]})

@app.route("/api/estado")
def estado():
    with lock:
        return jsonify({
            "next": state["next"],
            "queue": list(state["queue"]),
            "windows": list(state["windows"]),
            "active": list(state["active"]),
            "last_event": state["last_event"]
        })

@app.route("/api/reset", methods=["POST"])
def reset():
    with lock:
        state["next"] = 1
        state["queue"] = []
        state["windows"] = [None] * 8
        state["active"] = [True] * 8
        state["last_event"] = None
    return jsonify({"success": True})

if __name__ == "__main__":
    print("=" * 50)
    print("  SISTEMA DE TURNOS")
    print("  Pantalla:  http://localhost:5000")
    print("  Tecnico:   http://localhost:5000/tecnico")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
