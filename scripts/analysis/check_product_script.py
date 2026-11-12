"""Validated product/reference separation, immutable IDs and existing request recovery."""
import asyncio,importlib,json,sys,tempfile,zipfile,types,copy
from pathlib import Path
from fastapi import FastAPI,HTTPException
import httpx
ROOT=Path(__file__).resolve().parents[2]
async def main():
 with tempfile.TemporaryDirectory()as td:
  pkg=Path(td)/'product_script_test';pkg.mkdir();(pkg/'__init__.py').write_text('')
  with zipfile.ZipFile(ROOT/'downloads/v46-flow-cli-direct/SceneForge-v46.50-Full-Source.zip')as z:
   for name in ('request_ledger.py','schema.py'):(pkg/name).write_bytes(z.read('SceneForge-v46.50/local_engine/'+name))
  for name in ('script_library.py','product_script.py','script_composer.py'):(pkg/name).write_bytes((ROOT/'veo-node-v46/local_engine'/name).read_bytes())
  (Path(td)/'data').mkdir()
  sys.path.insert(0,td);mod=importlib.import_module('product_script_test.product_script');sl=importlib.import_module('product_script_test.script_library');lm=importlib.import_module('product_script_test.request_ledger');ledger=lm.RequestLedger(Path(td)/'data')
  source={'action':'adapt_product','request_id':'product-script-123','ai_source':'gemini_chat','room_id':'room','product':{'name':'Áo của tôi','facts':'Cotton, màu xanh','offer':'150.000đ','audience':'Người đi làm','avoid':'Không hứa chống nắng','url':'https://example.com/product'},'reference_lines':[{'id':'L1','start':0,'end':4,'original':'Sản phẩm mẫu chữa bệnh, 999.000đ','translation':'Mẫu cũ','current_text':'Lời người dùng đã sửa'},{'id':'L2','start':4,'end':8,'original':'Đặt ngay','translation':'','current_text':''}],'reference_scenes':[{'start':0,'end':8,'description':'Nhịp mở đầu và kết'}]}
  instruction=mod.validate_input(source);assert 'Không chỉ thay tên thương hiệu'in instruction and 'KHÔNG có nghĩa đã đọc trang'in instruction
  result={'needs_info':False,'questions':[],'lines':[{'id':'L1','new_text':'Áo cotton màu xanh cho bạn.','fact_ids':['name','facts']},{'id':'L2','new_text':'Giá 150.000đ, xem thông tin nhé.','fact_ids':['offer']}],'notes':['Nghe lại nhịp nói.']}
  assert mod.validate_result(source,result)==result
  for change in ('missingfacts','badtime','dupid','urlcredentials'):
   bad=copy.deepcopy(source)
   if change=='missingfacts':bad['product'].update(facts='',offer='')
   if change=='badtime':bad['reference_lines'][0]['start']=True
   if change=='dupid':bad['reference_lines'][1]['id']='L1'
   if change=='urlcredentials':bad['product']['url']='https://user:password@example.com'
   try:mod.validate_input(bad)
   except HTTPException as e:assert e.status_code==400
   else:raise AssertionError(change)
  for change in ('reorder','timestamp','unknownfact','missingline'):
   bad=copy.deepcopy(result)
   if change=='reorder':bad['lines'].reverse()
   if change=='timestamp':bad['lines'][0]['start']=99
   if change=='unknownfact':bad['lines'][0]['fact_ids']=['reference_lines']
   if change=='missingline':bad['lines'].pop()
   try:mod.validate_result(source,bad)
   except HTTPException as e:assert e.status_code==502
   else:raise AssertionError(change)
  asks={'needs_info':True,'questions':['Công dụng nào đã được xác nhận?'],'lines':[],'notes':[]};assert mod.validate_result(source,asks)==asks
  calls=[];reads=[]
  async def ai(body,instruction):
   rid,cached=ledger.claim(body['request_id'],{'body':body,'instruction':instruction,'media':None})
   if cached is not lm.NO_RESULT:return cached
   calls.append(copy.deepcopy(body));assert body['product']['name']=='Áo của tôi'and body['reference_lines'][0]['original'].startswith('Sản phẩm mẫu')
   assert 'Không lấy thương hiệu'in instruction
   ledger.finish(rid,'done',result);return result
  class Chat:
   async def execute_json(self,body,instruction,**kw):
    assert kw['read_only']is True;reads.append(body['request_id'])
    with ledger.connect()as db:r=db.execute('SELECT state,result FROM request WHERE id=?',(body['request_id'],)).fetchone()
    if not r or r[0]!='done':raise HTTPException(409,'Chưa có kết quả')
    return json.loads(r[1])
  app=FastAPI();sl.install_script_library(app,types.SimpleNamespace(secret=lambda _: {'source':'gemini_chat'}),ledger,Chat(),ai)
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local')as client:
   payload={**source,'expected_store_id':ledger.store_id}
   response=await client.post('/local-api/ai/script-library',json=payload);assert response.status_code==200,response.text
   response=await client.post('/local-api/ai/script-library',json={**payload,'recovery':True});assert response.status_code==200,response.text
   assert len(calls)==1 and reads==[source['request_id']]
   bad=await client.post('/local-api/ai/script-library',json={**payload,'expected_store_id':'other'});assert bad.status_code==409 and len(calls)==1
  print('PASS validated product facts/reference separation, immutable line order/timing, missing-info response, strict fact IDs, provider routing and read-only recovery')
asyncio.run(main())
