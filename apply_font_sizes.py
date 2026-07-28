with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Increase font sizes in TECH_PAGE CSS
replacements = [
    # Header name
    (".header .name { color:#3b82f6; font-size:1.2em; letter-spacing:2px; text-shadow:0 0 15px rgba(59,130,246,0.2); }",
     ".header .name { color:#3b82f6; font-size:1.8em; letter-spacing:2px; text-shadow:0 0 15px rgba(59,130,246,0.2); }"),
    
    # Status bar label
    (".status-bar .label { color:#b0c4d8; font-size:0.9em; letter-spacing:1px; }",
     ".status-bar .label { color:#b0c4d8; font-size:1.3em; letter-spacing:1px; }"),
    
    # Pending item position
    (".pend-item .pos { color:#8ab4c8; font-size:0.9em; }",
     ".pend-item .pos { color:#8ab4c8; font-size:1.2em; }"),
    
    # Pending item number (the main turn number)
    (".pend-item .num { font-size:1.6em; font-weight:bold; text-shadow:0 0 12px rgba(59,130,246,0.25); }",
     ".pend-item .num { font-size:2.5em; font-weight:bold; text-shadow:0 0 12px rgba(59,130,246,0.25); }"),
    
    # Empty pending text
    (".empty-pend { color:#4a6a8a; text-align:center; padding:25px; font-size:1em; letter-spacing:1px; }",
     ".empty-pend { color:#4a6a8a; text-align:center; padding:25px; font-size:1.5em; letter-spacing:1px; }"),
    
    # Button
    (".btn { width:100%; padding:16px; background:linear-gradient(135deg,#2563eb,#1d4ed8); color:#fff; border:none; border-radius:8px; font-family:inherit; font-size:1.2em; font-weight:bold; cursor:pointer; letter-spacing:2px; text-transform:uppercase; transition:.3s; box-shadow:0 0 20px rgba(59,130,246,0.12); margin-top:12px; }",
     ".btn { width:100%; padding:16px; background:linear-gradient(135deg,#2563eb,#1d4ed8); color:#fff; border:none; border-radius:8px; font-family:inherit; font-size:1.8em; font-weight:bold; cursor:pointer; letter-spacing:2px; text-transform:uppercase; transition:.3s; box-shadow:0 0 20px rgba(59,130,246,0.12); margin-top:12px; }"),
    
    # Attendance label
    (".asist-tech .lbl { color:#4a6a8a; font-size:0.8em; letter-spacing:1px; width:100%; text-align:center; margin-bottom:4px; }",
     ".asist-tech .lbl { color:#4a6a8a; font-size:1.2em; letter-spacing:1px; width:100%; text-align:center; margin-bottom:4px; }"),
    
    # Attendance buttons
    (".asist-tech button { padding:4px 10px; border-radius:6px; border:2px solid #1a3a8a; background:#050510; color:#4a6a8a; font-family:inherit; font-size:0.75em; cursor:pointer; transition:.3s; letter-spacing:1px; }",
     ".asist-tech button { padding:6px 12px; border-radius:6px; border:2px solid #1a3a8a; background:#050510; color:#4a6a8a; font-family:inherit; font-size:1.1em; cursor:pointer; transition:.3s; letter-spacing:1px; }"),
    
    # Off message
    (".off-msg { color:#ef4444; font-size:0.9em; margin:12px 0; text-shadow:0 0 10px rgba(239,68,68,0.2); }",
     ".off-msg { color:#ef4444; font-size:1.3em; margin:12px 0; text-shadow:0 0 10px rgba(239,68,68,0.2); }"),
    
    # Back link
    (".back { display:block; text-align:center; margin-top:18px; color:#4a6a8a; text-decoration:none; font-size:0.85em; letter-spacing:1px; transition:.3s; }",
     ".back { display:block; text-align:center; margin-top:18px; color:#4a6a8a; text-decoration:none; font-size:1.2em; letter-spacing:1px; transition:.3s; }"),
]

for old, new in replacements:
    if old in code:
        code = code.replace(old, new)
        print(f"Replaced: {new[:50]}...")
    else:
        print(f"NOT FOUND: {old[:50]}...")

with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("\nAll font size changes applied")