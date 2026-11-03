"""Read allowlisted original-CLI log events from its own stderr. No SDK patch or polling RPC."""
import asyncio
from collections import deque
import json
import re
import time

UUID=re.compile(r'^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$')
STARTED={'migrated.submit_observed','migrated.video_adopted_from_listing','migrated.video_adopted_from_status'}

class ProgressMismatch(RuntimeError):pass

class CliProgress:
    def __init__(self,service,rid,project):
        self.service,self.rid,self.project=service,rid,project
        self.dispatched=False;self.identity=None;self.last=None

    def update(self,state,message,status=None,event=None):
        if self.last and self.last[0] in ('downloading','validating') and state not in ('downloading','validating'):return
        signature=(state,status,self.identity and self.identity['media_id'],self.identity and self.identity['workflow_id'])
        if signature==self.last:return
        self.last=signature
        if self.identity:
            self.service.ledger.set_metadata(self.rid,{'provider_task':{**self.identity,'association_confirmed':True,
                'source':'gflow_cli_live','state':state,'provider_status':status,'observed_at':time.time()},
                'cli_live_event':event})
        self.service.phase(self.rid,state,message)

    def observe(self,value):
        if not isinstance(value,dict):return
        event=value.get('event')
        if event=='migrated.dispatch':
            if value.get('project_id')!=self.project:raise ProgressMismatch('CLI báo dự án khác lượt đã gửi; dừng theo dõi, không tự tạo lại.')
            self.dispatched=True
            self.update('opening','CLI đang chuẩn bị đúng dự án Flow.',event=event)
        elif event in ('migrated.frame_uploaded','migrated.references_attached','migrated.frame_bound',
                       'ui_automation_video.reference_attached','ui_automation_video.frame_attached'):
            if not self.identity:self.update('uploading','Ảnh tham chiếu đã gắn; CLI đang chuẩn bị lệnh tạo.',event=event)
        elif event=='migrated.submit_clicked':
            self.update('submitting','CLI đã bấm tạo; đang chờ Flow trả ID video.',event=event)
        elif event in STARTED:
            if not self.dispatched:return
            media=value.get('media_id');workflow=value.get('workflow_id')
            if not isinstance(media,str) or not UUID.fullmatch(media):return
            if self.identity and self.identity['media_id']!=media:raise ProgressMismatch('CLI báo nhiều ID video cho lượt x1; dừng, không tự tạo lại.')
            self.identity={'media_id':media,'project_id':self.project,
                'workflow_id':workflow if isinstance(workflow,str) and UUID.fullmatch(workflow) else (self.identity or {}).get('workflow_id')}
            self.status(value.get('status'),event)
        elif event=='migrated.status' and self.identity:
            self.status(value.get('status'),event)
        elif event=='migrated.result' and self.identity and value.get('done') is True:
            self.update('downloading','Flow đã tạo xong video; CLI đang tải về.',3,event)
        elif event=='migrated.download' and self.identity:
            self.update('validating','CLI đã tải tệp; đang kiểm tra và nhập về cảnh.',3,event)
        elif event=='ui_automation_video.poll_terminal':
            media=value.get('media_name')
            if not self.identity and isinstance(media,str) and UUID.fullmatch(media):
                self.identity={'media_id':media,'project_id':self.project,'workflow_id':None}
            if self.identity and self.identity['media_id']==media:
                self.update('downloading','CLI đã nhận trạng thái kết thúc của video; đang nhận kết quả.',value.get('status'),event)

    def status(self,value,event):
        if type(value) is not int:return self.update('waiting','Đã nhận ID video; đang chờ trạng thái Flow.',event=event)
        if value==6:self.update('waiting','Flow đã nhận video và trả ID; đang chờ xử lý.',value,event)
        elif value==2:self.update('generating','Flow đang tạo video; ID tác vụ đã được ghi nhận.',value,event)
        elif value==3:self.update('downloading','Flow đã tạo xong video; CLI đang tải về.',value,event)
        else:self.update('waiting','Flow trả trạng thái '+str(value)+'; đang chờ CLI xác nhận kết quả.',value,event)


async def communicate_live(process,monitor):
    """Drain both pipes concurrently. INFO logs are reduced to public event fields."""
    async def read(stream,is_stderr):
        chunks=deque();size=0;pending=b'';dropping=False
        def keep(data):
            nonlocal size
            chunks.append(data);size+=len(data)
            while size>4*1024**2 and len(chunks)>1:size-=len(chunks.popleft())
        def line(data):
            try:value=json.loads(data)
            except (ValueError,UnicodeError):keep(data);return
            if is_stderr and isinstance(value,dict):
                monitor.observe(value)
                if value.get('level') in ('info','debug'):
                    # Retain only the monitor's public event/ID/status fields, never raw INFO payloads.
                    if value.get('event') in STARTED|{'migrated.dispatch','migrated.status','migrated.result','migrated.download','migrated.submit_clicked','migrated.frame_uploaded','migrated.references_attached','migrated.frame_bound','ui_automation_video.poll_terminal'}:
                        public={'event':value['event'],'level':value['level']}
                        for key in ('media_id','workflow_id','project_id'):
                            if isinstance(value.get(key),str) and UUID.fullmatch(value[key]):public[key]=value[key]
                        if type(value.get('status')) is int:public['status']=value['status']
                        keep((json.dumps(public)+'\n').encode())
                    return
            keep(data)
        while chunk:=await stream.read(65536):
            if not is_stderr:keep(chunk);continue
            if dropping:
                cut=chunk.find(b'\n')
                if cut<0:continue
                chunk=chunk[cut+1:];dropping=False
            pending+=chunk
            while b'\n' in pending:
                item,pending=pending.split(b'\n',1);line(item+b'\n')
            if len(pending)>1024**2:pending=b'';dropping=True
        if pending:line(pending)
        return b''.join(chunks)
    tasks=[asyncio.create_task(read(process.stdout,False)),asyncio.create_task(read(process.stderr,True)),asyncio.create_task(process.wait())]
    try:
        stdout,stderr,_=await asyncio.gather(*tasks)
        return stdout,stderr
    finally:
        for task in tasks:
            if not task.done():task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
