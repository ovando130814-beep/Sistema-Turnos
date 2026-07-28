import urllib.request, urllib.parse, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open('https://sistema-turnos-iliy.onrender.com/tecnico', urllib.parse.urlencode({'username': 'Yesica Bonilla'}).encode())
resp = opener.open('https://sistema-turnos-iliy.onrender.com/tecnico/4')
html = resp.read().decode('utf-8', errors='replace')

with open(r'C:\Users\Administrador\Desktop\Sistema de Turnos\tech_deploy.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Saved tech_deploy.html')