with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Find the second TECH_PAGE definition and replace within it
# The second TECH_PAGE starts at "TECH_PAGE = \"\"\"" (the second occurrence)
first_idx = code.find('TECH_PAGE = """')
second_idx = code.find('TECH_PAGE = """', first_idx + 1)

if second_idx == -1:
    print("ERROR: Could not find second TECH_PAGE")
else:
    # Work on the section from second_idx onwards
    before = code[:second_idx]
    section = code[second_idx:]
    
    old_order = '''    <div class="section-header">🟡 EN ATENCIÓN</div>
    <div class="pend-list" id="currentList" style="max-height:120px;">
      <div class="empty-pend">NINGÚN TURNO EN ATENCIÓN</div>
    </div>
    <div class="divider"></div>
    <div class="section-header">🔴 EN ESPERA</div>
    <div class="pend-list" id="pendList">
      <div class="empty-pend"><span class="led"></span>SIN TURNOS EN ESPERA</div>
    </div>
    <div class="divider"></div>
    <div class="section-header">🟢 ATENDIDOS</div>'''
    
    new_order = '''    <div class="section-header">🔴 EN ESPERA</div>
    <div class="pend-list" id="pendList">
      <div class="empty-pend"><span class="led"></span>SIN TURNOS EN ESPERA</div>
    </div>
    <div class="divider"></div>
    <div class="section-header">🟡 EN ATENCIÓN</div>
    <div class="pend-list" id="currentList" style="max-height:120px;">
      <div class="empty-pend">NINGÚN TURNO EN ATENCIÓN</div>
    </div>
    <div class="divider"></div>
    <div class="section-header">🟢 ATENDIDOS</div>'''
    
    if old_order in section:
        section = section.replace(old_order, new_order, 1)  # Replace only first occurrence in this section
        code = before + section
        print("Reordered sections in second TECH_PAGE")
    else:
        print("Pattern not found in second TECH_PAGE")
        # Let's check what's actually there
        import re
        match = re.search(r'section-header.*ATENDIDOS', section, re.DOTALL)
        if match:
            print("Found section headers:", match.group()[:200])

with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'w', encoding='utf-8') as f:
    f.write(code)

# Verify
with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Check the order in the second TECH_PAGE
first_idx = code.find('TECH_PAGE = """')
second_idx = code.find('TECH_PAGE = """', first_idx + 1)
section = code[second_idx:]

espera_pos = section.find('🔴 EN ESPERA')
atencion_pos = section.find('🟡 EN ATENCIÓN')
atendidos_pos = section.find('🟢 ATENDIDOS')

print(f"EN ESPERA position: {espera_pos}")
print(f"EN ATENCIÓN position: {atencion_pos}")
print(f"ATENDIDOS position: {atendidos_pos}")

if espera_pos < atencion_pos < atendidos_pos:
    print("ORDER CORRECT: Espera -> Atención -> Atendidos")
else:
    print("ORDER INCORRECT")