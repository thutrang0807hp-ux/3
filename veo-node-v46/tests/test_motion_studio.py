"""Real local MP4 cut/package tests. No Google account or network generation."""
import asyncio
import base64
import importlib.util
import io
import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
import httpx
from fastapi import FastAPI,HTTPException
from PIL import Image

ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('motion_local_test',ROOT/'local_engine/motion_studio.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

@unittest.skipUnless(shutil.which('ffmpeg')and shutil.which('ffprobe'),'FFmpeg required')
class LocalMotion(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  source=self.root/'source.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=180x320:r=24','-f','lavfi','-i','sine=frequency=400:sample_rate=44100','-t','4','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(source)],check=True)
  self.raw=source.read_bytes();self.app=FastAPI();self.service=m.install_motion_studio(self.app,self.root)
  self.client=httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app),base_url='http://test')
 async def asyncTearDown(self):await self.client.aclose();self.temp.cleanup()
 async def upload(self,room='room-a'):
  r=await self.client.post('/local-api/motion-studio/sources',content=self.raw,headers={'X-Motion-Room':room,'Content-Type':'video/mp4'});self.assertEqual(r.status_code,200,r.text);return r.json()
 async def test_real_cut_cache_pack_and_room_isolation(self):
  source=await self.upload();self.assertAlmostEqual(source['duration'],4,delta=.1)
  body=dict(room_id='room-a',scene_id='scene-a',part_id='a',source_id=source['id'],start=1,end=3)
  r=await self.client.post('/local-api/motion-studio/clips',json=body);self.assertEqual(r.status_code,200,r.text);clip=r.json();self.assertAlmostEqual(clip['duration'],2,delta=.3)
  r=await self.client.post('/local-api/motion-studio/clips',json=body);self.assertEqual(r.json()['id'],clip['id'])
  r=await self.client.get('/local-api/motion-studio/clips/'+clip['id'],params={'room_id':'room-b'});self.assertEqual(r.status_code,409)
  image=io.BytesIO();Image.new('RGB',(16,16),'green').save(image,format='PNG');ref=dict(role='person',mime_type='image/png',data=base64.b64encode(image.getvalue()).decode())
  r=await self.client.post('/local-api/motion-studio/package',json=dict(room_id='room-a',clip_id=clip['id'],prompt_en='Replace the person. Preserve motion.',references=[ref]));self.assertEqual(r.status_code,200,r.text)
  with zipfile.ZipFile(io.BytesIO(r.content))as z:
   self.assertEqual(set(z.namelist()),{'source-clip.mp4','01-person.png','prompt-en.txt','reference-map.json'})
   self.assertEqual(z.read('01-person.png'),image.getvalue())
   self.assertEqual(json.loads(z.read('reference-map.json'))['scene_id'],'scene-a')
  self.assertFalse(list(self.service.root.glob('mpack-*.zip')))
  other=await self.upload('room-b');await self.client.post('/local-api/motion-studio/clear',json={'room_id':'room-a'})
  self.assertTrue((self.service.root/(other['id']+'.src')).exists())
  self.assertEqual((self.root/'source.mp4').read_bytes(),self.raw)
 async def test_bad_media_bad_bounds_and_traversal_do_not_cut(self):
  r=await self.client.post('/local-api/motion-studio/sources',content=b'not media',headers={'X-Motion-Room':'room-a'});self.assertEqual(r.status_code,422)
  self.assertFalse(list(self.service.root.glob('*.src')))
  source=await self.upload()
  base=dict(room_id='room-a',scene_id='scene-a',part_id='a',source_id=source['id'],start=0,end=4)
  for change in [{'start':-1},{'end':20},{'end':True},{'source_id':'../../outside'},{'room_id':'room-b'}]:
   r=await self.client.post('/local-api/motion-studio/clips',json={**base,**change});self.assertIn(r.status_code,(400,409))
  with self.assertRaises(HTTPException):await self.service.cut({**base,'end':float('nan')})
  self.assertFalse(list(self.service.root.glob('mclip-*.mp4')))

if __name__=='__main__':unittest.main()
