with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add pending_start to state
code = code.replace(
    '"attendance": {}, "current": [None] * 8, "current_start": [None] * 8,',
    '"attendance": {}, "current": [None] * 8, "current_start": [None] * 8, "pending_start": [[] for _ in range(8)],'
)

# 2. Update check_day to reset pending_start
code = code.replace(
    'state["current"] = [None] * 8\n        state["current_start"] = [None] * 8\n        state["attended"] = [[] for _ in range(8)]',
    'state["current"] = [None] * 8\n        state["current_start"] = [None] * 8\n        state["attended"] = [[] for _ in range(8)]\n        state["pending_start"] = [[] for _ in range(8)]'
)

# 3. Update tomar_turno to record timestamp
old_turno = '''        state["pending"][ventanilla].append(num)
        broadcast({"type": "nuevo", "num": num, "ventanilla": ventanilla + 1, "ts": time.time()})'''

new_turno = '''        state["pending"][ventanilla].append(num)
        state["pending_start"][ventanilla].append(time.time())
        broadcast({"type": "nuevo", "num": num, "ventanilla": ventanilla + 1, "ts": time.time()})'''

code = code.replace(old_turno, new_turno)

# 4. Update atender_siguiente to remove from pending_start when popping
old_atender = '''        num = state["pending"][ventanilla - 1].pop(0)
        state["current"][ventanilla - 1] = num
        state["current_start"][ventanilla - 1] = time.time()'''

new_atender = '''        num = state["pending"][ventanilla - 1].pop(0)
        state["pending_start"][ventanilla - 1].pop(0)
        state["current"][ventanilla - 1] = num
        state["current_start"][ventanilla - 1] = time.time()'''

code = code.replace(old_atender, new_atender)

# 5. Update toggle_tecnico to clear pending_start
code = code.replace(
    'state["pending"][ventanilla - 1] = []\n            state["current"][ventanilla - 1] = None\n            state["current_start"][ventanilla - 1] = None',
    'state["pending"][ventanilla - 1] = []\n            state["pending_start"][ventanilla - 1] = []\n            state["current"][ventanilla - 1] = None\n            state["current_start"][ventanilla - 1] = None'
)

# 6. Update reset to clear pending_start
code = code.replace(
    'state["current"] = [None] * 8\n        state["current_start"] = [None] * 8\n        state["last_event"] = None',
    'state["current"] = [None] * 8\n        state["current_start"] = [None] * 8\n        state["pending_start"] = [[] for _ in range(8)]\n        state["last_event"] = None'
)

# 7. Add pending_start to estado response
code = code.replace(
    '"current": list(state["current"]), "current_start": list(state["current_start"])',
    '"current": list(state["current"]), "current_start": list(state["current_start"]), "pending_start": [list(q) for q in state["pending_start"]]'
)

# 8. Update central panel render to show wait time
# Find the central panel render function and add wait time display
old_central_render = '''         '<div class="pend">En espera: ' + pend.length + '</div>' +
         '<div class="att">Atendidos: ' + (data.attended[i] || []).length + '</div>' +
         (data.current && data.current[i] ? '<div class="timer">⏱️ ' + formatTime(data.current_start && data.current_start[i] ? Math.floor((Date.now()/1000) - data.current_start[i]) : 0) + '</div>' : '')'''

new_central_render = '''         '<div class="pend">En espera: ' + pend.length + '</div>' +
         '<div class="att">Atendidos: ' + (data.attended[i] || []).length + '</div>' +
         (data.current && data.current[i] ? '<div class="timer">⏱️ Atendiendo: ' + formatTime(data.current_start && data.current_start[i] ? Math.floor((Date.now()/1000) - data.current_start[i]) : 0) + '</div>' : '') +
         (pend.length > 0 ? '<div class="wait">⏳ Espera: ' + formatTime(data.pending_start && data.pending_start[i] ? Math.floor((Date.now()/1000) - data.pending_start[i][0]) : 0) + '</div>' : '')'''

code = code.replace(old_central_render, new_central_render)

# 9. Add CSS for wait time in central panel
code = code.replace(
    '.card .timer { color:#fbbf24; font-weight:bold; font-size:0.85em; margin-top:2px; }',
    '.card .timer { color:#fbbf24; font-weight:bold; font-size:0.85em; margin-top:2px; }\n  .card .wait { color:#ef4444; font-weight:bold; font-size:0.85em; margin-top:2px; }'
)

with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('All wait time changes applied')
print('Has pending_start:', '"pending_start"' in code)
print('Has pending_start in estado:', '"pending_start": [list(q)' in code)
print('Has wait CSS:', '.card .wait' in code)
print('Has Espera in central:', 'Espera:' in code)