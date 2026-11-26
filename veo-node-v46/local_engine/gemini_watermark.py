"""Offline visible Gemini star processing; original assets are never overwritten."""
import asyncio,base64,io,subprocess,tempfile,os
from pathlib import Path
from fastapi import HTTPException
from PIL import Image
TOOL=Path(__file__).resolve().parents[1]/'vendor/gemini-watermark-0.3.2/GeminiWatermarkTool.exe'

def process(encoded, *, tool=TOOL, runner=None):
 try:
  if not isinstance(encoded,str)or len(encoded)>22*1024**2:raise ValueError()
  raw=base64.b64decode(encoded,validate=True)
  if not 0<len(raw)<=15*1024**2:raise ValueError()
  with Image.open(io.BytesIO(raw))as im:
   if im.format not in ('PNG','JPEG','WEBP')or im.width*im.height>16000000 or max(im.size)>8192:raise ValueError()
   size=im.size;im.load();image=im.convert('RGBA'if 'A'in im.getbands()else'RGB')
 except Exception:raise HTTPException(400,'Chọn ảnh PNG/JPEG/WebP gốc tối đa 15 MB, 16 triệu điểm ảnh.')from None
 if not tool.is_file():raise HTTPException(503,'Thiếu công cụ xóa logo Gemini. Cài lại bản cập nhật; ảnh gốc vẫn giữ nguyên.')
 try:
  with tempfile.TemporaryDirectory(prefix='sceneforge-watermark-')as folder:
   source=Path(folder)/'original.png';output=Path(folder)/'cleaned.png';image.save(source,'PNG')
   result=(runner or subprocess.run)([str(tool),'--input',source.name,'--output',output.name],cwd=folder,timeout=30,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**({'creationflags':0x08000000}if os.name=='nt'else{}))
   if result.returncode==1:return {'changed':False,'message':'Không phát hiện dấu sao Gemini có thể xử lý; giữ nguyên ảnh.'}
   if result.returncode!=0 or not output.is_file()or not 0<output.stat().st_size<=15*1024**2:raise ValueError()
   data=output.read_bytes()
   with Image.open(io.BytesIO(data))as checked:
    if checked.format!='PNG'or checked.size!=size:raise ValueError()
    checked.verify()
   return {'changed':True,'image':base64.b64encode(data).decode('ascii'),'mime_type':'image/png','width':size[0],'height':size[1]}
 except Exception:raise HTTPException(502,'Không xử lý được logo Gemini. Ảnh gốc vẫn được giữ nguyên.')from None

def install_watermark(app):
 slot=asyncio.Semaphore(1)
 @app.post('/local-api/gemini-chat/remove-watermark')
 async def remove(body:dict):
  async with slot:return await asyncio.to_thread(process,body.get('image'))
