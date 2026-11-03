"""Allowlisted status events and public-ID projection from a live child process."""
import asyncio,importlib.util,json,sys,types,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('cli_progress',Path(__file__).parents[1]/'local_engine/flow_cli_progress.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PROJECT='11111111-1111-4111-8111-111111111111';MEDIA='22222222-2222-4222-8222-222222222222';WORKFLOW='33333333-3333-4333-8333-333333333333'
def fixture():
 meta={}
 service=types.SimpleNamespace(ledger=types.SimpleNamespace(set_metadata=lambda rid,value:meta.update(value)),phase=lambda rid,phase,message:meta.update(phase=phase,message=message))
 return m.CliProgress(service,'request',PROJECT),meta
class ProgressTests(unittest.IsolatedAsyncioTestCase):
 def test_no_image_ids_or_unscoped_ids(self):
  monitor,meta=fixture();monitor.observe(dict(event='migrated.frame_uploaded',media_id=MEDIA));monitor.observe(dict(event='migrated.submit_observed',media_id=MEDIA,status=6))
  self.assertNotIn('provider_task',meta)
 def test_real_status_stages_do_not_regress_or_fake_percent(self):
  monitor,meta=fixture();monitor.observe(dict(event='migrated.dispatch',project_id=PROJECT));monitor.observe(dict(event='migrated.submit_observed',media_id=MEDIA,workflow_id=WORKFLOW,status=6))
  for status,phase in [(2,'generating'),(3,'downloading'),(2,'downloading')]:
   monitor.observe(dict(event='migrated.status',status=status));self.assertEqual(meta['phase'],phase)
  self.assertEqual(meta['provider_task']['media_id'],MEDIA);self.assertEqual(meta['provider_task']['workflow_id'],WORKFLOW);self.assertNotIn('progress',meta)
 def test_wrong_project_stops_monitor(self):
  monitor,meta=fixture()
  with self.assertRaises(m.ProgressMismatch):monitor.observe(dict(event='migrated.dispatch',project_id='other'))
 async def test_pipe_info_redaction_and_no_deadlock(self):
  monitor,meta=fixture()
  events=[dict(event='migrated.dispatch',level='info',project_id=PROJECT,session='SECRET_SESSION'),dict(event='migrated.submit_observed',level='info',media_id=MEDIA,workflow_id=WORKFLOW,status=6,signed_url='SECRET_URL'),dict(event='unrelated',level='info',token='SECRET_TOKEN')]
  script='import sys,json\nfor e in '+repr(events)+':print(json.dumps(e),file=sys.stderr,flush=True)\nprint("{}")'
  process=await asyncio.create_subprocess_exec(sys.executable,'-c',script,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
  stdout,stderr=await m.communicate_live(process,monitor)
  self.assertEqual(stdout,b'{}\n');self.assertNotIn(b'SECRET_',stderr);self.assertIn(MEDIA.encode(),stderr);self.assertEqual(meta['provider_task']['media_id'],MEDIA)
if __name__=='__main__':unittest.main()
