with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Remove the asist-tech section from HTML
old_html = '''    <div class="divider"></div>
    <div class="asist-tech" id="asistTech">
      <div class="lbl">📍 MI ASISTENCIA:</div>
    </div>
    <div class="divider"></div>

    <div class="pend-list" id="pendList">'''

new_html = '''    <div class="divider"></div>
    <div class="pend-list" id="pendList">'''

code = code.replace(old_html, new_html)

# 2. Remove asistOpts array and asist-related functions
old_js_start = '''  const asistOpts = [
    {key:'sede', lbl:'🏢 Sede', cls:'sede'},
    {key:'movil', lbl:'🚐 Móvil', cls:'movil'},
    {key:'mision', lbl:'🏛️ M. Oficial', cls:'mision'},
    {key:'ausente', lbl:'❌ Ausente', cls:'ausente'},
    {key:'incapacidad', lbl:'🏥 Incapacidad', cls:'incapacidad'},
    {key:'consulta', lbl:'📋 Consulta', cls:'consulta'}
  ];
  function initAsist() {
    fetch('/api/estado').then(r=>r.json()).then(data => {
      const val = (data.attendance_today || {})[v-1] || 'sede';
      renderAsist(val);
    }).catch(e => console.error('initAsist error:', e));
  }
  function renderAsist(val) {
    const container = document.getElementById('asistTech');
    if (!container) return;
    let html = '<div class="lbl">📍 MI ASISTENCIA:</div>';
    asistOpts.forEach(o => {
      const btn = document.createElement('button');
      btn.className = val === o.key ? 'on ' + o.cls : '';
      btn.textContent = o.lbl;
      btn.onclick = function() { setAsist(o.key); };
      container.appendChild(btn);
    });
    container.innerHTML = html;
  }
  function setAsist(tipo) {
    const obj = {}; obj[v-1] = tipo;
    fetch('/api/asistencia', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({registro: obj})})
      .then(r=>r.json()).then(d => {
        if (d.success) { renderAsist(tipo); }
      }).catch(e => console.error('setAsist error:', e));
  }
  function render(data) {'''

new_js_start = '''  function render(data) {'''

code = code.replace(old_js_start, new_js_start)

# 3. Remove the initAsist() call from the initialization line
code = code.replace(
    '  initAsist(); actualizar(); setInterval(actualizar, 3000);',
    '  actualizar(); setInterval(actualizar, 3000);'
)

# 4. Add a section header for "En atención" before the pending list
old_pending = '''    <div class="pend-list" id="pendList">
      <div class="empty-pend"><span class="led"></span>SIN TURNOS EN ESPERA</div>
    </div>
    <div class="divider"></div>
    <div class="pend-list" id="attendedList" style="max-height:160px;">
      <div class="empty-pend" style="color:#22c55e;">SIN ATENDIDOS</div>
    </div>'''

new_pending = '''    <div class="section-header">🟡 EN ATENCIÓN</div>
    <div class="pend-list" id="currentList" style="max-height:120px;">
      <div class="empty-pend">NINGÚN TURNO EN ATENCIÓN</div>
    </div>
    <div class="divider"></div>
    <div class="section-header">🔴 EN ESPERA</div>
    <div class="pend-list" id="pendList">
      <div class="empty-pend"><span class="led"></span>SIN TURNOS EN ESPERA</div>
    </div>
    <div class="divider"></div>
    <div class="section-header">🟢 ATENDIDOS</div>
    <div class="pend-list" id="attendedList" style="max-height:160px;">
      <div class="empty-pend" style="color:#22c55e;">SIN ATENDIDOS</div>
    </div>'''

code = code.replace(old_pending, new_pending)

# 5. Add CSS for section headers
old_css = '.divider { height:1px; background:linear-gradient(90deg,transparent,rgba(59,130,246,0.15),transparent); margin:10px 0; }'
new_css = '.divider { height:1px; background:linear-gradient(90deg,transparent,rgba(59,130,246,0.15),transparent); margin:10px 0; }\n  .section-header { color:#60a5fa; font-size:1.1em; font-weight:bold; letter-spacing:1px; margin:8px 0 4px 0; text-align:left; padding-left:4px; }'
code = code.replace(old_css, new_css)

# 6. Update the render function to populate the current list
old_render_current = '''      pend.forEach((n, idx) => {
          const item = document.createElement('div');
          item.className = n === currentNum ? 'pend-item active' : 'pend-item pending';'''

new_render_current = '''      const currentList = document.getElementById('currentList');
      if (currentList) {
        currentList.innerHTML = '';
        if (currentNum !== null && currentNum !== undefined) {
          const cItem = document.createElement('div');
          cItem.className = 'pend-item active';
          cItem.innerHTML = '<span class="pos">EN ATENCIÓN</span><span class="num">' + currentNum + '</span>';
          currentList.appendChild(cItem);
        } else {
          currentList.innerHTML = '<div class="empty-pend">NINGÚN TURNO EN ATENCIÓN</div>';
        }
      }
      pend.forEach((n, idx) => {
          const item = document.createElement('div');
          item.className = n === currentNum ? 'pend-item active' : 'pend-item pending';'''

code = code.replace(old_render_current, new_render_current)

with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Changes applied successfully')
print('Has section-header CSS:', '.section-header' in code)
print('Has currentList:', 'currentList' in code)
print('Has EN ATENCION:', 'EN ATENCIÓN' in code)
print('Removed asistOpts:', 'asistOpts' not in code)
print('Removed initAsist:', 'initAsist' not in code)