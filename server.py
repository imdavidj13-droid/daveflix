import json, sqlite3, pathlib, re, mimetypes, webbrowser, secrets, hmac, sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
ROOT=pathlib.Path(__file__).resolve().parent
DB=ROOT/'daveflix.db'
CONFIG=ROOT/'connection.json'
KEY_FILE=ROOT/'pairing.key'
ALLOWED_ORIGINS={'http://127.0.0.1:8787','http://localhost:8787'}
TOKEN=''
def connection_init():
 global TOKEN
 if not KEY_FILE.exists(): KEY_FILE.write_text(secrets.token_urlsafe(32))
 TOKEN=KEY_FILE.read_text().strip()
 if CONFIG.exists():
  origin=json.loads(CONFIG.read_text()).get('website_origin','')
  if origin: ALLOWED_ORIGINS.add(origin)

def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init():
 with db() as c:
  c.executescript('CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT); CREATE TABLE IF NOT EXISTS media(id INTEGER PRIMARY KEY,path TEXT UNIQUE,title TEXT,series TEXT,season INTEGER,episode INTEGER,position REAL DEFAULT 0,duration REAL DEFAULT 0,saved INTEGER DEFAULT 0,available INTEGER DEFAULT 1);')
def scan(folder):
 p=pathlib.Path(folder).expanduser().resolve()
 if not p.is_dir(): raise ValueError('That folder does not exist. Enter the full Windows folder path.')
 files=[f for f in p.rglob('*') if f.is_file() and f.suffix.lower() in ('.mp4','.m4v','.webm','.mkv','.mov','.avi')]
 with db() as c:
  c.execute("INSERT OR REPLACE INTO settings VALUES('folder',?)",(str(p),)); c.execute('UPDATE media SET available=0')
  for f in files:
   name=f.stem; m=re.search(r'(.+?)[ ._-]*S(\d{1,2})E(\d{1,3})',name,re.I)
   series=re.sub(r'[._]',' ',m[1]).strip() if m else ''
   title=re.sub(r'[._]',' ',name).strip()
   c.execute('INSERT INTO media(path,title,series,season,episode) VALUES(?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET available=1,title=excluded.title,series=excluded.series,season=excluded.season,episode=excluded.episode',(str(f.resolve()),title,series,int(m[2]) if m else 0,int(m[3]) if m else 0))
 return len(files)
class Handler(BaseHTTPRequestHandler):
 def log_message(self,fmt,*args):
  # Native media requests contain a pairing key. Never log query strings.
  print('%s %s' % (self.command,urlparse(self.path).path))
 def end_headers(self):
  origin=self.headers.get('Origin')
  if origin in ALLOWED_ORIGINS:
   self.send_header('Access-Control-Allow-Origin',origin)
   self.send_header('Vary','Origin')
   self.send_header('Access-Control-Expose-Headers','Content-Range,Accept-Ranges,Content-Length')
  self.send_header('Cache-Control','no-store')
  self.send_header('Referrer-Policy','no-referrer')
  super().end_headers()
 def authorized(self):
  origin=self.headers.get('Origin')
  if origin and origin not in ALLOWED_ORIGINS:
   self.reply({'error':'Website address not allowed. Configure this website origin on your PC.'},403); return False
  supplied=self.headers.get('Authorization','').removeprefix('Bearer ') or parse_qs(urlparse(self.path).query).get('key',[''])[0]
  if not TOKEN or not hmac.compare_digest(supplied,TOKEN):
   self.reply({'error':'Pairing key missing or incorrect.'},401); return False
  return True
 def do_OPTIONS(self):
  if self.headers.get('Origin') not in ALLOWED_ORIGINS: return self.reply({'error':'Origin rejected'},403)
  self.send_response(204)
  self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
  self.send_header('Access-Control-Allow-Headers','Authorization,Content-Type,Range')
  self.end_headers()
 def reply(self,data,status=200):
  b=json.dumps(data).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
 def do_POST(self):
  if not self.authorized(): return
  try:
   size=int(self.headers.get('Content-Length','0'))
   if size>10000: raise ValueError('Request too large')
   data=json.loads(self.rfile.read(size)); route=urlparse(self.path).path
   if route=='/api/scan': return self.reply({'count':scan(data['folder'])})
   if route=='/api/update':
    with db() as c:
     if 'saved' in data: c.execute('UPDATE media SET saved=? WHERE id=?',(int(bool(data['saved'])),int(data['id'])))
     else: c.execute('UPDATE media SET position=?,duration=? WHERE id=?',(max(0,float(data['position'])),max(0,float(data['duration'])),int(data['id'])))
    return self.reply({'ok':True})
   self.reply({'error':'Not found'},404)
  except Exception as e: self.reply({'error':str(e)},400)
 def do_GET(self):
  route=urlparse(self.path).path
  if route.startswith(('/api/','/stream/','/subtitle/')) and not self.authorized(): return
  if route=='/api/library':
   with db() as c:
    rows=[dict(r) for r in c.execute('SELECT id,title,series,season,episode,position,duration,saved FROM media WHERE available=1 ORDER BY series,season,episode,title')]; s=c.execute("SELECT value FROM settings WHERE key='folder'").fetchone()
   return self.reply({'items':rows,'folder':s[0] if s else ''})
  if route.startswith('/stream/') or route.startswith('/subtitle/'):
   try:
    ident=int(route.rsplit('/',1)[1])
    with db() as c: row=c.execute('SELECT path FROM media WHERE id=? AND available=1',(ident,)).fetchone()
    if not row: return self.send_error(404)
    f=pathlib.Path(row[0])
    if route.startswith('/subtitle/'):
     f=f.with_suffix('.vtt')
     if not f.is_file(): return self.send_error(404)
    return self.file(f)
   except (ValueError,FileNotFoundError): return self.send_error(404)
  if route in ('/','/app.js','/connection-store.js','/style.css'): return self.file(ROOT/'public'/('index.html' if route=='/' else route[1:]))
  self.send_error(404)
 def file(self,p):
  size=p.stat().st_size; start=0; end=size-1; partial=False
  r=self.headers.get('Range')
  if r:
   m=re.fullmatch(r'bytes=(\d*)-(\d*)',r)
   if not m or not any(m.groups()): return self.send_error(416)
   if m[1]: start=int(m[1]); end=min(int(m[2]),size-1) if m[2] else size-1
   else: start=max(0,size-int(m[2]))
   if start>end or start>=size:
    self.send_response(416); self.send_header('Content-Range',f'bytes */{size}'); self.end_headers(); return
   partial=True
  self.send_response(206 if partial else 200); self.send_header('Content-Type','text/vtt' if p.suffix=='.vtt' else mimetypes.guess_type(str(p))[0] or 'application/octet-stream'); self.send_header('Accept-Ranges','bytes'); self.send_header('Content-Length',str(end-start+1))
  if partial: self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
  self.end_headers()
  try:
   with p.open('rb') as f:
    f.seek(start); remaining=end-start+1
    while remaining:
     chunk=f.read(min(1024*1024,remaining))
     if not chunk: break
     self.wfile.write(chunk); remaining-=len(chunk)
  except (BrokenPipeError,ConnectionResetError): pass
if __name__=='__main__':
 if '--configure' in sys.argv:
  origin=input('Paste your deployed DAVEFLIX website URL: ').strip().rstrip('/')
  u=urlparse(origin)
  if u.scheme!='https' or not u.netloc or u.path or u.query or u.fragment or u.username:
   raise SystemExit('Enter only the HTTPS website origin, for example https://daveflix.example.workers.dev')
  CONFIG.write_text(json.dumps({'website_origin':origin},indent=2))
 if '--background' in sys.argv:
  log=(ROOT/'server.log').open('a',buffering=1,encoding='utf-8')
  sys.stdout=log;sys.stderr=log
 connection_init(); init()
 # Bind before announcing startup, so a second instance cannot appear healthy.
 try: http=ThreadingHTTPServer(('127.0.0.1',8787),Handler)
 except OSError as error: raise SystemExit('DAVEFLIX could not start. Port 8787 may already be in use: '+str(error))
 print('DAVEFLIX PC server: http://127.0.0.1:8787')
 if '--background' not in sys.argv: print('Pairing key (keep private): '+TOKEN)
 print('Keep this window open while watching.')
 if '--background' not in sys.argv: webbrowser.open('http://127.0.0.1:8787')
 http.serve_forever()
