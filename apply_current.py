# Apply full current-attending state
with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add "current": [None] * 8 to state
code = code.replace(
    '"attendance": {},',
    '"attendance": {}, "current": [None] * 8,'
)

# 2. Update check_day to reset current
code = code.replace(
    'state["attended"] = [[] for _ in range(8)]',
    'state["attended"] = [[] for _ in range(8)]\n        state["current"] = [None] * 8'
)

# 3. Update atender_siguiente to use current
old = '''num = state["pending"][ventanilla - 1].pop(0)
        state["attended"][ventanilla - 1].append(num)
        broadcast({"type": "llamada", "num": num, "ventanilla": ventanilla, "ts": time.time()})'''

new = '''prev = state["current"][ventanilla - 1]
        if prev is not None:
            state["attended"][ventanilla - 1].append(prev)
        num = state["pending"][ventanilla - 1].pop(0)
        state["current"][ventanilla - 1] = num
        broadcast({"type": "llamada", "num": num, "ventanilla": ventanilla, "ts": time.time()})'''

code = code.replace(old, new)

# 4. Add current to estado response
code = code.replace(
    '"attendance_today": state["attendance"].get(str(date.today()), {})',
    '"attendance_today": state["attendance"].get(str(date.today()), {}), "current": list(state["current"])'
)

# 5. Update toggle_tecnico to clear current when deactivating
code = code.replace(
    'if not state["active"][ventanilla - 1]:\n            state["pending"][ventanilla - 1] = []',
    'if not state["active"][ventanilla - 1]:\n            state["pending"][ventanilla - 1] = []\n            state["current"][ventanilla - 1] = None'
)

# 6. Update reset to clear current
code = code.replace(
    'state["last_event"] = None',
    'state["current"] = [None] * 8\n        state["last_event"] = None'
)

# 7. Update render JS to show current turn in yellow and pending in red
# Remove the previous active class change first, then apply new logic
old_js = '''pend.forEach((n, idx) => {
          const item = document.createElement('div');
          item.className = idx === 0 ? 'pend-item active' : 'pend-item pending';'''

new_js = '''const currentNum = data.current ? data.current[v-1] : null;
      pend.forEach((n, idx) => {
          const item = document.createElement('div');
          item.className = n === currentNum ? 'pend-item active' : 'pend-item pending';'''

code = code.replace(old_js, new_js)

with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('All changes applied')
print('Has current in state:', '"current": [None]' in code)
print('Has current in check_day:', 'state["current"] = [None] * 8' in code)
print('Has current in atender:', 'state["current"][ventanilla - 1] = num' in code)
print('Has current in estado:', '"current": list(state["current"])' in code)
print('Has current in JS:', 'const currentNum' in code)