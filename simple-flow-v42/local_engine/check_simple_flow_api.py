"""Real app routes, local auth and lifecycle; browser process is mocked."""
import os,tempfile,time
from pathlib import Path
from unittest.mock import patch,Mock
from fastapi.testclient import TestClient

def main():
 with tempfile.TemporaryDirectory()as tmp:
  os.environ['SCENEFORGE_LOCAL_DATA']=tmp
  from . import server
  process=Mock();process.poll.return_value=None
  with patch.object(server.SIMPLE_FLOW,'find_browser',return_value=Path('/fixture/edge')),patch('subprocess.Popen',return_value=process)as launch:
   with TestClient(server.app)as client:
    client.get('/');headers={'X-SceneForge-Local':'1'}
    assert client.get('/local-api/flow/status').json()['connection_method']=='simple_flow'
    assert server.SIMPLE_FLOW.context is None
    response=client.post('/local-api/flow/simple/connect',headers=headers,json={'browser':'msedge'});assert response.status_code==200,response.text
    for _ in range(100):
     status=client.get('/local-api/flow/simple/status').json()
     if status.get('interaction'):break
     time.sleep(.01)
    assert status['interaction']['kind']=='login'and server.SIMPLE_FLOW.pw is None
    assert client.post('/local-api/flow/simple/respond',headers=headers,json={'id':'wrong','accept':True}).status_code==409
    assert client.post('/local-api/flow/simple/mode',headers=headers,json={'mode':'legacy'}).status_code==409
    assert client.post('/local-api/flow/simple/stop',headers=headers,json={}).status_code==200
    assert client.post('/local-api/flow/simple/mode',headers=headers,json={'mode':'legacy'}).status_code==200
    assert client.post('/local-api/flow/simple/mode',headers=headers,json={'mode':'simple'}).status_code==200
    assert launch.call_count==1
  for handler in list(server.RUNTIME_LOG.handlers):handler.close();server.RUNTIME_LOG.removeHandler(handler)
  server.LIBRARY._root_guard.instance.close()
 print('PASS app API: simple mode default, lazy browser, auth routes before frontend, one explicit login launch, stale confirmation/mode switch blocked, stop and mode rollback; no real browser or Google calls.')
if __name__=='__main__':main()
