# -*- coding: utf-8 -*-
"""
Sistema de Turnos de Espera
8 ventanillas, voz en espanol cuando hay nuevo turno.
"""

import threading
import json
import time
from flask import Flask, render_template_string, request, jsonify, Response

app = Flask(__name__)

# Estado en memoria (simple)
lock = threading.Lock()
state = {
    "next": 1,
    "queue": [],          # turnos en espera
    "windows": [None] * 8,  # turno actual por ventanilla (1-8)
    "last_event": None,   # {type, num, ventanilla, ts}
}

def broadcast_event(event):
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
  .waiting { background:#334155; padding:10px 30px; text-align:center; font-size:1.5em; }
  .waiting b { color:#fbbf24; font-size:1.6em; }
  .grid { display:grid; grid-template-columns:repeat(4,1fr); gap:20px; padding:30px; }
  .win { background:#1e293b; border-radius:20px; padding:25px; text-align:center; border:3px solid #334155; min-height:160px; }
  .win.active { border-color:#22c55e; box-shadow:0 0 30px rgba(34,197,94,.4); }
  .win .num { font-size:3.5em; font-weight:bold; color:#fbbf24; }
  .win .lbl { font-size:1em; color:#94a3b8; margin-top:10px; }
  .win .empty { color:#64748b; font-size:2em; }
  .footer { text-align:center; padding:20px; color:#64748b; }
  .btn-turno { display:block; width:300px; margin:0 auto 20px; padding:18px; background:#38bdf8; color:#0f172a; border:none; border-radius:15px; font-size:1.4em; font-weight:bold; cursor:pointer; }
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
  <div class="grid" id="grid"></div>
  <div class="footer">Tu turno aparecera en la pantalla. Escuche su numero.</div>

<script>
  let ultimoTs = null;

  function tomarTurno() {
    fetch('/api/tomar_turno', {method:'POST'}).then(r=>r.json()).then(d=>{
      if (d.success) alert('Tu turno es: ' + d.num + '\\nEspera a que te llamen.');
    });
  }

  function hablar(num, vent) {
    if ('speechSynthesis' in window) {
      const txt = 'Turno ' + num + ', pase a ventanilla ' + vent;
      const u = new SpeechSynthesisUtterance(txt);
      u.lang = 'es-ES';
      u.rate = 0.95;
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
      const div = document.createElement('div');
      div.className = 'win' + (t ? ' active' : '');
      if (t) {
        div.innerHTML = '<div class="num">' + t + '</div><div class="lbl">Ventanilla ' + (i+1) + '</div>';
      } else {
        div.innerHTML = '<div class="empty">---</div><div class="lbl">Ventanilla ' + (i+1) + '</div>';
      }
      grid.appendChild(div);
    }
  }

  function actualizar() {
    fetch('/api/estado').then(r=>r.json()).then(data=>{
      render(data);
      if (data.last_event && data.last_event.ts !== ultimoTs && data.last_event.type === 'llamada') {
        ultimoTs = data.last_event.ts;
        hablar(data.last_event.num, data.last_event.ventanilla);
      }
    });
  }

  // Reloj
  setInterval(()=>{ document.getElementById('clock').textContent = new Date().toLocaleTimeString('es-ES'); }, 1000);

  // Polling cada 1s
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
  .top { text-align:center; margin-bottom:20px; }
  .top h1 { color:#0f172a; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:15px; max-width:1000px; margin:0 auto; }
  .card { background:#fff; border-radius:15px; padding:20px; text-align:center; box-shadow:0 3px 10px rgba(0,0,0,.1); }
  .card .vnum { font-size:1em; color:#64748b; }
  .card .current { font-size:3em; font-weight:bold; color:#0ea5e9; margin:10px 0; }
  .card .current.none { color:#cbd5e1; }
  .btn { width:100%; padding:12px; background:#22c55e; color:#fff; border:none; border-radius:10px; font-size:1em; font-weight:bold; cursor:pointer; margin-top:10px; }
  .btn:hover { background:#16a34a; }
  .btn:disabled { background:#cbd5e1; cursor:not-allowed; }
  .waiting { text-align:center; margin-bottom:15px; color:#475569; font-size:1.1em; }
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
      const div = document.createElement('div');
      div.className = 'card';
      div.innerHTML = '<div class="vnum">Ventanilla ' + (i+1) + '</div>' +
        '<div class="current ' + (t ? '' : 'none') + '">' + (t ? t : '---') + '</div>' +
        '<button class="btn" onclick="llamar(' + (i+1) + ')" ' + (data.queue.length===0 && !t ? 'disabled' : '') + '>📢 Llamar siguiente</button>';
      grid.appendChild(div);
    }
  }

  function llamar(v) {
    fetch('/api/llamar_siguiente/' + v, {method:'POST'}).then(r=>r.json()).then(d=>{
      if (d.success) actualizar();
    });
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
        broadcast_event({"type": "nuevo", "num": num, "ventanilla": None, "ts": time.time()})
    return jsonify({"success": True, "num": num})

@app.route("/api/llamar_siguiente/<int:ventanilla>", methods=["POST"])
def llamar_siguiente(ventanilla):
    if not 1 <= ventanilla <= 8:
        return jsonify({"success": False, "error": "Ventanilla invalida"})
    with lock:
        if not state["queue"]:
            return jsonify({"success": False, "error": "No hay turnos en espera"})
        num = state["queue"].pop(0)
        state["windows"][ventanilla - 1] = num
        broadcast_event({"type": "llamada", "num": num, "ventanilla": ventanilla, "ts": time.time()})
    return jsonify({"success": True, "num": num, "ventanilla": ventanilla})

@app.route("/api/estado")
def estado():
    with lock:
        return jsonify({
            "next": state["next"],
            "queue": list(state["queue"]),
            "windows": list(state["windows"]),
            "last_event": state["last_event"]
        })

@app.route("/api/reset", methods=["POST"])
def reset():
    with lock:
        state["next"] = 1
        state["queue"] = []
        state["windows"] = [None] * 8
        state["last_event"] = None
    return jsonify({"success": True})

if __name__ == "__main__":
    print("=" * 50)
    print("  SISTEMA DE TURNOS")
    print("  Pantalla:  http://localhost:5000")
    print("  Tecnico:   http://localhost:5000/tecnico")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
