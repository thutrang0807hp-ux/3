"""Local Motion Studio clip preparation. No cloud submission or account handling."""
import asyncio
import base64
import hashlib
import io
import json
import math
from pathlib import Path
import re
import secrets
import shutil
import time
import zipfile
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

MAX_SOURCE=128*1024**2
MAX_TEMP=384*1024**2
TTL=3600


def text_id(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',value):
        raise HTTPException(400,'Sai mã phòng/cảnh Motion Studio.')
    return value


class MotionStudio:
    def __init__(self,root):
        self.root=Path(root)/'motion-studio-temp';self.root.mkdir(parents=True,exist_ok=True)
        self.gate=asyncio.Lock();self.cleanup()

    def cleanup(self):
        for path in self.root.iterdir():
            if path.is_file() and path.name.startswith(('msrc-','mclip-','mpack-')) and time.time()-path.stat().st_mtime>TTL:
                path.unlink(missing_ok=True)

    def used(self):return sum(p.stat().st_size for p in self.root.iterdir() if p.is_file())

    def record(self,key,room):
        text_id(room)
        if not isinstance(key,str) or not re.fullmatch(r'(?:msrc|mclip)-[a-f0-9]{32}',key):raise HTTPException(400,'Sai mã tệp Motion Studio.')
        try:data=json.loads((self.root/(key+'.json')).read_text())
        except (OSError,ValueError):raise HTTPException(404,'Tệp tạm đã hết hạn; chuẩn bị lại trên máy, không gửi AI.') from None
        if data['room_id']!=room:raise HTTPException(409,'Tệp thuộc phòng khác.')
        if time.time()-data['at']>TTL:raise HTTPException(410,'Tệp tạm đã hết hạn.')
        return data

    async def command(self,*args,timeout=120):
        process=await asyncio.create_subprocess_exec(*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        try:
            out,err=await asyncio.wait_for(process.communicate(),timeout)
            if process.returncode:raise HTTPException(422,'Không đọc/cắt được video nguồn. Giữ file gốc; chưa gửi AI.')
            return out
        finally:
            if process.returncode is None:
                process.kill();await process.communicate()

    async def probe(self,path):
        raw=await self.command('ffprobe','-v','error','-protocol_whitelist','file,pipe','-show_entries','stream=codec_type,width,height:format=duration,format_name','-of','json',str(path),timeout=30)
        try:
            data=json.loads(raw);video=next(s for s in data['streams'] if s['codec_type']=='video')
            fmt=data['format'].get('format_name','')
            if not any(t in fmt.split(',') for t in ('mp4','mov','webm','matroska')):raise ValueError()
            duration=float(data['format']['duration']);width=int(video['width']);height=int(video['height'])
            if not math.isfinite(duration) or not 0<duration<=600 or width<=0 or height<=0 or max(width,height)>3840 or width*height>3840*2160:raise ValueError()
            return dict(duration=duration,width=width,height=height)
        except (KeyError,ValueError,TypeError,StopIteration):raise HTTPException(422,'Video thiếu thời lượng/kích thước hợp lệ.') from None

    async def upload(self,request):
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):raise HTTPException(409,'Cần FFmpeg trong app để cắt video mẫu.')
        room=text_id(request.headers.get('x-motion-room'))
        async with self.gate:
            self.cleanup()
            if self.used()+MAX_SOURCE>MAX_TEMP:raise HTTPException(409,'Vùng tạm Motion Studio gần đầy. Dọn bộ tạm trong nhánh rồi thử lại.')
            key='msrc-'+secrets.token_hex(16);path=self.root/(key+'.src');total=0;digest=hashlib.sha256()
            try:
                with path.open('wb') as stream:
                    async for chunk in request.stream():
                        total+=len(chunk)
                        if total>MAX_SOURCE:raise HTTPException(413,'Video mẫu tối đa 128 MB cho lượt chuẩn bị này.')
                        digest.update(chunk);stream.write(chunk)
                info=await self.probe(path)
                data=dict(id=key,room_id=room,sha256=digest.hexdigest(),bytes=total,at=time.time(),**info)
                (self.root/(key+'.json')).write_text(json.dumps(data));return data
            except BaseException:path.unlink(missing_ok=True);raise

    async def cut(self,body):
        room=text_id(body.get('room_id'));text_id(body.get('scene_id'));text_id(body.get('part_id'))
        source=self.record(body.get('source_id'),room)
        try:
            start=body['start'];end=body['end']
            if type(start)not in (int,float)or type(end)not in (int,float)or not all(math.isfinite(x)for x in (start,end))or start<0 or end>source['duration']+.1 or not .2<=end-start<=15:raise ValueError()
        except (KeyError,TypeError,ValueError):raise HTTPException(400,'Mốc clip cần nằm trong nguồn, dài từ 0,2 đến 15 giây.') from None
        key='mclip-'+hashlib.sha256(json.dumps([source['sha256'],room,body['scene_id'],body['part_id'],start,end,'h264-crf18-v1'],separators=(',',':')).encode()).hexdigest()[:32]
        async with self.gate:
            self.cleanup();target=self.root/(key+'.mp4')
            if target.is_file() and (self.root/(key+'.json')).is_file():return self.record(key,room)
            if self.used()+MAX_SOURCE>MAX_TEMP:raise HTTPException(409,'Vùng tạm Motion Studio gần đầy; dọn bộ tạm rồi thử lại.')
            temp=self.root/(key+'.partial.mp4')
            try:
                await self.command('ffmpeg','-v','error','-nostdin','-y','-protocol_whitelist','file,pipe','-ss',str(start),'-i',str(self.root/(source['id']+'.src')),'-t',str(end-start),'-map','0:v:0','-map','0:a:0?','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-avoid_negative_ts','make_zero',str(temp))
                if temp.stat().st_size>MAX_SOURCE:raise HTTPException(413,'Clip tạm vượt giới hạn 128 MB.')
                info=await self.probe(temp)
                if abs(info['duration']-(end-start))>.3:raise HTTPException(422,'Clip cắt chưa khớp thời lượng yêu cầu.')
                temp.replace(target)
                data=dict(id=key,room_id=room,scene_id=body['scene_id'],part_id=body['part_id'],source_sha256=source['sha256'],start=start,end=end,bytes=target.stat().st_size,at=time.time(),**info)
                (self.root/(key+'.json')).write_text(json.dumps(data));return data
            finally:temp.unlink(missing_ok=True)

    async def package(self,body):
        room=text_id(body.get('room_id'));clip=self.record(body.get('clip_id'),room)
        prompt=body.get('prompt_en');refs=body.get('references')
        if not isinstance(prompt,str) or not prompt.strip()or len(prompt)>16000 or not isinstance(refs,list)or not 1<=len(refs)<=8:raise HTTPException(400,'Cần prompt Anh và 1–8 ảnh tham khảo.')
        prepared=[];total=0
        from PIL import Image
        for index,row in enumerate(refs):
            try:
                if row.get('role')not in ('person','outfit','product','background'):raise ValueError()
                raw=base64.b64decode(row['data'],validate=True);total+=len(raw)
                if not 0<len(raw)<=6*1024**2 or total>32*1024**2:raise ValueError()
                with Image.open(io.BytesIO(raw)) as image:
                    if image.width*image.height>40_000_000:raise ValueError()
                    mime=Image.MIME[image.format];image.verify()
                suffix={'image/png':'png','image/jpeg':'jpg','image/webp':'webp'}[mime]
                if row['mime_type']!=mime:raise ValueError()
                prepared.append((f'{index+1:02d}-{row["role"]}.{suffix}',raw,row['role']))
            except (KeyError,ValueError,TypeError,OSError):raise HTTPException(400,'Ảnh tham khảo không hợp lệ hoặc quá lớn.') from None
        async with self.gate:
            if self.used()+clip['bytes']+total>MAX_TEMP:raise HTTPException(409,'Vùng tạm không đủ chỗ tạo gói.')
            key='mpack-'+secrets.token_hex(16);path=self.root/(key+'.zip')
            try:
                with zipfile.ZipFile(path,'w',zipfile.ZIP_STORED)as archive:
                    archive.write(self.root/(clip['id']+'.mp4'),'source-clip.mp4')
                    for name,raw,_ in prepared:archive.writestr(name,raw)
                    archive.writestr('prompt-en.txt',prompt)
                    archive.writestr('reference-map.json',json.dumps(dict(room_id=room,scene_id=clip['scene_id'],part_id=clip['part_id'],references=[dict(file=n,role=r)for n,_,r in prepared]),ensure_ascii=False,indent=2))
                return FileResponse(path,media_type='application/zip',filename='Motion-Studio-'+clip['scene_id'][:20]+'-'+clip['part_id']+'.zip',background=BackgroundTask(path.unlink,missing_ok=True))
            except BaseException:path.unlink(missing_ok=True);raise

    async def clear(self,room):
        text_id(room)
        async with self.gate:
            count=0
            for path in self.root.glob('*.json'):
                try:data=json.loads(path.read_text())
                except (OSError,ValueError):continue
                if data.get('room_id')!=room:continue
                key=data['id']
                if not re.fullmatch(r'(?:msrc|mclip)-[a-f0-9]{32}',key):continue
                for ext in ('.src','.mp4','.json'):
                    p=self.root/(key+ext)
                    if p.exists():p.unlink();count+=1
            return {'removed_files':count}


def install_motion_studio(app,root):
    service=MotionStudio(root)
    @app.get('/local-api/motion-studio/status')
    async def status():
        if not service.gate.locked():service.cleanup()
        return dict(local_cut=bool(shutil.which('ffmpeg')and shutil.which('ffprobe')),automatic_flow_edit=False,max_source_bytes=MAX_SOURCE,temporary_bytes=service.used(),temporary_ttl_seconds=TTL)
    @app.post('/local-api/motion-studio/sources')
    async def source(request:Request):return await service.upload(request)
    @app.post('/local-api/motion-studio/clips')
    async def clip(body:dict):return await service.cut(body)
    @app.get('/local-api/motion-studio/clips/{key}')
    async def file(key:str,room_id:str):
        service.record(key,room_id)
        if not key.startswith('mclip-'):raise HTTPException(400,'Cần mã clip.')
        return FileResponse(service.root/(key+'.mp4'),media_type='video/mp4',filename='source-clip.mp4')
    @app.post('/local-api/motion-studio/package')
    async def package(body:dict):return await service.package(body)
    @app.post('/local-api/motion-studio/clear')
    async def clear(body:dict):return await service.clear(body.get('room_id'))
    return service
