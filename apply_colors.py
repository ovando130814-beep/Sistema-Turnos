with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    '.pend-item.pending .num { color:#ef4444; }',
    '.pend-item.active .num { color:#fbbf24; text-shadow:0 0 20px rgba(251,191,36,0.4); }\n  .pend-item.pending .num { color:#ef4444; }'
)

code = code.replace(
    "item.className = 'pend-item pending';",
    "item.className = idx === 0 ? 'pend-item active' : 'pend-item pending';"
)

with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Changes applied successfully')
print('First replacement found:', '.pend-item.pending .num' in code)
print('Second replacement found:', "idx === 0" in code)