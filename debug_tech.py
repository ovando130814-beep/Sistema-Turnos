import urllib.request, urllib.parse, http.cookiejar, re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
data = urllib.parse.urlencode({'username': 'Yesica Bonilla'}).encode()
opener.open('https://sistema-turnos-iliy.onrender.com/tecnico', data)
resp = opener.open('https://sistema-turnos-iliy.onrender.com/tecnico/4')
html = resp.read().decode('utf-8', errors='replace')

out = r'C:\Users\Administrador\Desktop\Sistema de Turnos\tech_debug.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

print('File saved:', out)
print('Size:', len(html))
print('Has pendList:', 'pendList' in html)
print('Has btnAtender:', 'btnAtender' in html)
print('Has