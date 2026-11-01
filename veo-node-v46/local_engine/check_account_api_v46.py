"""Real central account routes, shared Veo status, and no second login endpoint."""
import os,tempfile
from types import SimpleNamespace
from unittest.mock import patch,AsyncMock
from fastapi.testclient import TestClient

def main():
 with tempfile.TemporaryDirectory()as tmp:
  os.environ['SCENEFORGE_LOCAL_DATA']=tmp
  from . import server
  with TestClient(server.app)as client:
   client.get('/');headers={'X-SceneForge-Local':'1'}
   state=client.get('/local-api/flow/simple/status').json()
   assert state['shared_accounts']and state['background']and not state['selection']['available']
   server.VAULT.set_secret('flow-transport-v2',{'mode':'legacy'})
   assert client.get('/local-api/flow/simple/status').json()['enabled']
   assert client.post('/local-api/flow/simple/mode',headers=headers,json={'mode':'legacy'}).status_code==409
   assert client.post('/local-api/flow/simple/connect',headers=headers,json={}).status_code==409
   aid='flow-web-fixture'
   server.VAULT.put('accounts',{'id':aid,'service':'flow','name':'Fixture web','enabled':True,'session_verified':True,'state':'ready','active':False,'priority':0,'login_transport':'web_ui'})
   server.VAULT.set_secret('flow-managed-profiles',{aid:{'account_id':aid,'email':'fixture@invalid','profile_key':'fixture'}})
   selected=client.post('/local-api/flow/selection',headers=headers,json={'mode':'selected','account_id':aid})
   assert selected.status_code==200,selected.text
   shared=client.get('/local-api/flow/simple/status').json();normal=client.get('/local-api/flow/status').json()
   assert shared['selection']==selected.json()['selection']==normal['selection']
   with patch.object(server.FLOW_WEB_LOGIN,'start',new_callable=AsyncMock,return_value={'opened':True,'state':'waiting','message':'Fixture login'})as login:
    assert client.post('/local-api/flow/web-login',headers=headers,json={'new_profile':True}).status_code==200
    login.assert_awaited_once_with(new_profile=True)
    original=server.SIMPLE_FLOW.task;server.SIMPLE_FLOW.task=SimpleNamespace(done=lambda:False)
    try:assert client.post('/local-api/flow/web-login',headers=headers,json={}).status_code==409
    finally:server.SIMPLE_FLOW.task=original
    assert login.await_count==1
   server.SIMPLE_FLOW.tasks['flow-active-v45-test']=True
   assert client.post('/local-api/requests/flow-active-v45-test/abandon',headers=headers,json={'confirm_history_checked':True}).status_code==409
   server.SIMPLE_FLOW.tasks.clear()
   import io,time
   from PIL import Image
   rid='flow-preview-v46-fixture'
   with server.REQUESTS.connect()as db:db.execute('INSERT INTO request VALUES(?,?,?,?,?)',(rid,'fixture','failed',None,time.time()))
   server.REQUESTS.set_metadata(rid,{'transport':'simple_flow','has_preview':True})
   image=io.BytesIO();Image.new('RGB',(40,40),'green').save(image,format='PNG');(server.SIMPLE_FLOW.root/(rid+'.preview.png')).write_bytes(image.getvalue())
   response=client.get('/local-api/flow/simple/preview/'+rid)
   assert response.status_code==200 and response.content==image.getvalue()and response.headers.get('cache-control')=='no-store'
   current=server.REQUESTS.store_id
   base='/local-api/flow/simple/diagnostics/'
   report=client.get(base+rid,params={'store_id':current}).json()
   assert report['code']=='found'and report['record']['request_id']==rid and not report['can_retry']
   report=client.get(base+rid,params={'store_id':'old-store'}).json()
   assert report['code']=='different_store'and report['record']is None
   missing='flow-missing-diagnostic-fixture'
   assert client.get(base+missing,params={'store_id':current}).json()['code']=='missing_record'
   assert client.get(base+missing).json()['code']=='unknown_store'
   assert client.get(base+'invalid').status_code==400
   assert client.get(base+rid,params={'room_id':'another-room'}).json()['code']=='different_room'
   client.cookies.clear();assert client.get('/local-api/flow/simple/preview/'+rid).status_code in (401,403)
   assert client.get(base+rid).status_code in (401,403)
  for handler in list(server.RUNTIME_LOG.handlers):handler.close();server.RUNTIME_LOG.removeHandler(handler)
  server.LIBRARY._root_guard.instance.close()
 print('PASS v46 API: central selection equals Veo/provider selection, existing web-login route used, second SimpleFlow login rejected, login blocked during active generation, active receipt cannot be abandoned. No real browser/Google calls.')
if __name__=='__main__':main()
