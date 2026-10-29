import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

spec=importlib.util.spec_from_file_location('daveflix_server',Path(__file__).resolve().parents[1]/'server.py')
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

class ConnectionTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
  server.DB=self.root/'test.db'; server.TOKEN='test-pairing-key'
  server.ALLOWED_ORIGINS={'https://daveflix.example.workers.dev'}
  server.init(); (self.root/'Example S01E01.mp4').write_bytes(b'0123456789'); server.scan(str(self.root))
  self.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
  self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
  self.base='http://127.0.0.1:'+str(self.http.server_port)
 def tearDown(self):
  self.http.shutdown();self.http.server_close();self.thread.join();self.temp.cleanup()
 def request(self,path,headers=None,data=None,method=None):
  return urlopen(Request(self.base+path,headers=headers or {},data=data,method=method))
 def test_requires_key_on_library_and_stream(self):
  for path in ['/api/library','/stream/1','/subtitle/1']:
   with self.assertRaises(HTTPError) as e:self.request(path)
   self.assertEqual(e.exception.code,401)
 def test_cross_origin_library_and_partial_stream(self):
  headers={'Origin':'https://daveflix.example.workers.dev','Authorization':'Bearer test-pairing-key'}
  with self.request('/api/library',headers) as r:
   self.assertEqual(r.headers['Access-Control-Allow-Origin'],headers['Origin'])
   self.assertEqual(json.load(r)['items'][0]['series'],'Example')
  with self.request('/stream/1?key=test-pairing-key',{'Range':'bytes=3-6','Origin':headers['Origin']}) as r:
   self.assertEqual(r.status,206);self.assertEqual(r.read(),b'3456')
 def test_rejects_unapproved_origin_even_with_key(self):
  with self.assertRaises(HTTPError) as e:self.request('/api/library',{'Origin':'https://other.example','Authorization':'Bearer test-pairing-key'})
  self.assertEqual(e.exception.code,403)
 def test_preflight_and_progress(self):
  origin='https://daveflix.example.workers.dev'
  with self.request('/api/update',{'Origin':origin},method='OPTIONS') as r:self.assertEqual(r.status,204)
  data=json.dumps({'id':1,'position':42,'duration':100}).encode()
  with self.request('/api/update',{'Origin':origin,'Authorization':'Bearer test-pairing-key','Content-Type':'application/json'},data) as r:self.assertTrue(json.load(r)['ok'])
  with self.request('/api/library',{'Authorization':'Bearer test-pairing-key'}) as r:self.assertEqual(json.load(r)['items'][0]['position'],42)

if __name__=='__main__':unittest.main()
