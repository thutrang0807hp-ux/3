"""One private SDK child; no socket, no automatic synthesis retries, idle RAM release."""
import asyncio,json,os,signal,uuid
from pathlib import Path
class VoiceRuntime:
 def __init__(self,idle_seconds=180,timeout=1800):
  self.lock=asyncio.Lock();self.process=None;self.key=None;self.idle=None;self.phase='cold';self.idle_seconds=idle_seconds;self.timeout=timeout
 def status(self):return {'phase':self.phase,'warm':self.process is not None and self.process.returncode is None,'idle_release_seconds':self.idle_seconds}
 async def _stop(self):
  process=self.process;self.process=None;self.key=None;self.phase='cold'
  if process is None:return
  if process.returncode is None:
   if os.name=='nt':
    killer=await asyncio.create_subprocess_exec('taskkill','/PID',str(process.pid),'/T','/F',stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL);await killer.wait()
   else:
    try:os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError:pass
   if process.returncode is None:
    try:process.kill()
    except ProcessLookupError:pass
  await process.wait()
 async def close(self):
  if self.idle:self.idle.cancel();self.idle=None
  async with self.lock:await self._stop()
 async def _release_later(self,process):
  try:
   await asyncio.sleep(self.idle_seconds)
   async with self.lock:
    if self.process is process:await self._stop()
  except asyncio.CancelledError:pass
 async def execute(self,python,runtime,key,request,output,result):
  async with self.lock:
   if self.idle:self.idle.cancel();self.idle=None
   if self.key!=key or self.process is None or self.process.returncode is not None:
    await self._stop();self.phase='loading'
    try:self.process=await asyncio.create_subprocess_exec(str(python),'-u',str(Path(__file__).with_name('voice_runtime_worker.py')),'--runtime',str(runtime),stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,start_new_session=os.name!='nt')
    except BaseException:self.phase='cold';raise
    self.key=key
   else:self.phase='generating'
   process=self.process;nonce=str(uuid.uuid4())
   async def exchange():
    process.stdin.write((json.dumps({'nonce':nonce,'request':str(request),'output':str(output),'result':str(result)})+'\n').encode());await process.stdin.drain()
    line=await process.stdout.readline();reply=json.loads(line)
    if reply.get('nonce')!=nonce or not reply.get('ok'):raise RuntimeError('Voice worker failed')
   try:await asyncio.wait_for(exchange(),self.timeout)
   except BaseException:
    await self._stop();raise
   self.phase='ready';self.idle=asyncio.create_task(self._release_later(process))
RUNTIME=VoiceRuntime()
