import asyncio,importlib.util,io,subprocess,tempfile,unittest
from pathlib import Path
import httpx
from fastapi import FastAPI
from PIL import Image
spec=importlib.util.spec_from_file_location('frame_capture',Path(__file__).parents[1]/'local_engine/frame_capture.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class CaptureTest(unittest.IsolatedAsyncioTestCase):
 async def test_capture_and_rejections(self):
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder);video=root/'test.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=180x320:r=24','-t','2','-c:v','libx264','-pix_fmt','yuv420p',str(video)],check=True)
   app=FastAPI();module.install_frame_capture(app,root)
   async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local')as client:
    data=video.read_bytes();headers={'X-SceneForge-Local':'1','X-Frame-Time':'1'}
    response=await client.post('/local-api/analysis/frame-capture',content=data,headers=headers);self.assertEqual(response.status_code,200,response.text[:100]if response.status_code!=200 else '')
    with Image.open(io.BytesIO(response.content))as im:self.assertEqual(im.size,(180,320));self.assertGreater(im.getpixel((30,30))[2],200)
    for at in ['NaN','-1','1000','2']:
     r=await client.post('/local-api/analysis/frame-capture',content=data,headers={**headers,'X-Frame-Time':at});self.assertEqual(r.status_code,422)
    r=await client.post('/local-api/analysis/frame-capture',content=b'bad video',headers=headers);self.assertEqual(r.status_code,422)
    r=await client.post('/local-api/analysis/frame-capture',content=data);self.assertEqual(r.status_code,403)
   self.assertEqual(list((root/'frame-capture-temp').iterdir()),[])
if __name__=='__main__':unittest.main()
