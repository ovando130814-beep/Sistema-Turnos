with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Find and remove the asistencia section - it's between the asistOpts and the render function
# The block starts with "const asistOpts" and ends before "function render(data)"
import re

# Remove the entire asistencia block
pattern = r'  const asistOpts = \[.*?\]\n  function initAsistencia\(\) \{.*?\}\n  function renderAsistencia\(val\) \{.*?\}\n  function setAsistencia\(tipo\) \{.*?\}\n  '

match = re.search(pattern, code, re.DOTALL)
if match:
    code = code[:match.start()] + code[match.end():]
    print("Removed asistencia block")
else:
    print("Pattern not found, trying alternative...")
    # Try to find the block manually
    start = code.find('  const asistOpts = [')
    end = code.find('  function render(data) {')
    if start >= 0 and end >= 0:
        code = code[:start] + code[end:]
        print("Removed asistencia block (manual)")

# Also remove the initAsistencia() call
code = code.replace('  initAsistencia(); actualizar(); setInterval(actualizar, 1500);', '  actualizar(); setInterval(actualizar, 1500);')

# Verify
print('asistOpts in code:', 'asistOpts' in code)
print('initAsistencia in code:', 'initAsistencia' in code)
print('renderAsistencia in code:', 'renderAsistencia' in code)
print('setAsistencia in code:', 'setAsistencia' in code)

with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Done")