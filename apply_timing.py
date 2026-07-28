import re

with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add current_start to state
code = code.replace(
    '"attendance": {}, "current": [None] * 8,',
    '"attendance": {}, "current": [None] * 8, "current_start": [None] * 8,'
)

# 2. Update check_day to reset current_start
code = code.replace(
    'state["current"] = [None] * 8\n        state["attended"] = [[] for _ in range(8)]',
    'state["current"] = [None] * 8\n        state["current_start"] = [None] * 8\n        state["attended"] = [[] for _ in range(8)]'
)

# 3. Update atender_siguiente to record start time
code = code.replace(
    'state["current"][ventanilla - 1] = num\n        broadcast({"type": "llamada", "num": num, "ventanilla": ventanilla, "ts": time.time()})',
    'state["current"][ventanilla - 1] = num\n        state["current_start"][ventanilla - 1] = time.time()\n        broadcast({"type": "llamada", "num": num, "ventanilla": ventanilla, "ts": time.time()})'
)

# 4. Add current_start to estado response
code = code.replace(
    '"current": list(state["current"])',
    '"current": list(state["current"]), "current_start": list(state["current_start"])'
)

# 5. Update toggle_tecnico to clear current_start
code = code.replace(
    'state["current"][ventanilla - 1] = None',
    'state["current"][ventanilla - 1] = None\n            state["current_start"][ventanilla - 1] = None'
)

# 6. Update reset to clear current_start
code = code.replace(
    'state["current"] = [None] * 8\n        state["last_event"] = None',
    'state["current"] = [None] * 8\n        state["current_start"] = [None] * 8\n        state["last_event"] = None'
)

# 7. Update TECH_PAGE render JS to show time and colors
# Add time display in the status bar
code = code.replace(
    '<span class="label">👤 Tienes <strong id="count">0</strong> usuarios en espera</span>',
    '<span class="label">👤 Tienes <strong id="count">0</strong> usuarios en espera</span><span class="label" style="margin-left:10px;">⏱️ En atención: <strong id="timer">0:00</strong></span>'
)

# Update render function to show current turn in yellow and time
old_render = '''      pend.forEach((n, idx) => {
          const item = document.createElement('div');
          item.className = n === currentNum ? 'pend-item active' : 'pend-item pending';'''

new_render = '''      const currentNum = data.current ? data.current[v-1] : null;
      const currentStart = data.current_start ? data.current_start[v-1] : null;
      if (currentStart) {
        const elapsed = Math.floor((Date.now() / 1000) - currentStart);
        const mins = Math.floor(elapsed / 60);
        const secs = elapsed % 60;
        const timerEl = document.getElementById('timer');
        if (timerEl) timerEl.textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;
      }
      pend.forEach((n, idx) => {
          const item = document.createElement('div');
          item.className = n === currentNum ? 'pend-item active' : 'pend-item pending';'''

code = code.replace(old_render, new_render)

# 8. Update central panel to show current turn time
# Find the central panel render function and add time display
old_central = '''<div class="vnum">' + techNames[i] + '</div>' +
         '<div class="current ' + (first ? '' : 'none') + '">' + (first ? first : '---') + '</div>' +
         '<div class="pend">En espera: ' + pend.length + '</div>' +
         '<div class="att">Atendidos: ' + (data.attended[i] || []).length + '</div>'''

new_central = '''<div class="vnum">' + techNames[i] + '</div>' +
         '<div class="current ' + (first ? '' : 'none') + '">' + (first ? first : '---') + '</div>' +
         '<div class="pend">En espera: ' + pend.length + '</div>' +
         '<div class="att">Atendidos: ' + (data.attended[i] || []).length + '</div>' +
         (data.current && data.current[i] ? '<div class="timer">⏱️ ' + formatTime(data.current_start && data.current_start[i] ? Math.floor((Date.now()/1000) - data.current_start[i]) : 0) + '</div>' : '')'''

code = code.replace(old_central, new_central)

# 9. Add formatTime helper function in central panel JS
code = code.replace(
    'function render(data) {\n    const grid = document.getElementById(\'grid\'); grid.innerHTML = \'\';',
    'function formatTime(seconds) {\n    const m = Math.floor(seconds / 60);\n    const s = seconds % 60;\n    return m + \':\' + (s < 10 ? \'0\' : \'\') + s;\n  }\n  function render(data) {\n    const grid = document.getElementById(\'grid\'); grid.innerHTML = \'\';'
)

# 10. Add CSS for timer in central panel
code = code.replace(
    '.card .att { color:#3b82f6; font-weight:bold; }',
    '.card .att { color:#3b82f6; font-weight:bold; }\n  .card .timer { color:#fbbf24; font-weight:bold; font-size:0.85em; margin-top:2px; }'
)

# 11. Add CSS for active (yellow) in tech panel - make sure it's there
code = code.replace(
    '.pend-item.active .num { color:#fbbf24; text-shadow:0 0 20px rgba(251,191,36,0.4); }',
    '.pend-item.active .num { color:#fbbf24; text-shadow:0 0 20px rgba(251,191,36,0.4); }\n  .pend-item.active { background:rgba(251,191,36,0.05); border-color:rgba(251,191,36,0.3); }'
)

with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('All timing changes applied successfully')
print('Has current_start:', '"current_start"' in code)
print('Has timer element:', 'id="timer"' in code)
print('Has formatTime:', 'function formatTime' in code)
print('Has timer CSS:', '.card .timer' in code)
print('Has active CSS:', '.pend-item.active' in code)