with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix duplicate currentNum declaration
code = code.replace(
    "const currentNum = data.current ? data.current[v-1] : null;\n      const currentNum = data.current ? data.current[v-1] : null;",
    "const currentNum = data.current ? data.current[v-1] : null;"
)

with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'w', encoding='utf-8') as f:
    f.write(code)

# Verify fix
with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'r', encoding='utf-8') as f:
    code = f.read()

count = code.count("const currentNum = data.current ? data.current[v-1] : null;")
print(f"currentNum declarations: {count}")
if count == 1:
    print("FIXED - only one declaration now")
else:
    print("STILL BROKEN - need to fix manually")