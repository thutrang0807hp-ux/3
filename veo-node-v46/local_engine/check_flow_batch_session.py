"""Execute shared transport with fixture browser globals and stub fetch only."""
import json
import subprocess
import unittest

from .flow_batch_session import batch_script

PROJECT = '11111111-1111-4111-8111-111111111111'
MEDIA = '22222222-2222-4222-8222-222222222222'


def fixture(scope, calls, *, wiz=None, entries=None, at_input=None, response_size=0):
    data={'scope':scope,'calls':calls,'project':PROJECT,'media':MEDIA,
          'wiz':{'cfb2h':'BUILD','SNlM0e':'PRIVATE_AT','FdrFJe':'PRIVATE_SID'} if wiz is None else wiz,
          'entries':entries or [],'at_input':at_input,'response_size':response_size}
    js=r'''
const f=FIXTURE;
globalThis.window={WIZ_global_data:f.wiz};
globalThis.location={origin:'https://flow.google.com',pathname:'/project/'+f.project};
globalThis.document={querySelector:s=>s==='input[name="at"]'&&f.at_input?{value:f.at_input}:null};
Object.defineProperty(globalThis,'performance',{value:{getEntriesByType:()=>f.entries.map(name=>({name}))},configurable:true});
Object.defineProperty(globalThis,'crypto',{value:{randomUUID:()=> '33333333-3333-4333-8333-333333333333'},configurable:true});
Date.now=()=>1000;
const requests=[],results=[];
globalThis.fetch=async(url,options)=>{
    requests.push({url:String(url),credentials:options.credentials,referrer:options.referrer,
        form:Object.fromEntries(new URLSearchParams(options.body))});
    let sent=false;
    return {status:200,body:{getReader:()=>({cancel:async()=>{},read:async()=>{
        if(sent||!f.response_size)return {done:true};sent=true;return {done:false,value:new Uint8Array(f.response_size)};
    }})}};
};
const send=(SCRIPT);
for(const call of f.calls){
    if(call.prepareKey)window[call.key]={project:f.project,token:'PRIVATE_VERIFY',action:call.prepareKey,created:1000};
    results.push(await send({project:f.project,media:f.media,...call}));
}
process.stdout.write(JSON.stringify({requests,results}));
'''.replace('const f=FIXTURE;','const f='+json.dumps(data)+';').replace('(SCRIPT)','('+batch_script(scope)+')')
    result=subprocess.run(['node','--input-type=module','-e',js],capture_output=True,text=True,timeout=10)
    if result.returncode:
        raise AssertionError(result.stderr[:700])
    return json.loads(result.stdout)


class TransportCases(unittest.TestCase):
    def test_generation_has_shared_locale_referrer_and_cookies(self):
        out=fixture('generation',[{'key':'proof','prepareKey':'VIDEO_GENERATION','prompt':'Wave.'}])
        self.assertEqual(len(out['requests']),1)
        request=out['requests'][0]
        self.assertIn('hl=en-GB',request['url'])
        self.assertEqual(request['credentials'],'include')
        self.assertEqual(request['referrer'],'https://flow.google.com/project/'+PROJECT)
        payload=json.loads(json.loads(request['form']['f.req'])[0][0][1])
        self.assertEqual(payload[0][0][2:4],['veo_3_1_r2v_lite',1])
        self.assertNotIn('PRIVATE_AT',json.dumps(out['results']))
        self.assertNotIn('PRIVATE_VERIFY',json.dumps(out['results']))

    def test_context_fallback_uses_same_project_observation(self):
        url='https://flow.google.com/_/AiSandboxAngularFrontend/data/batchexecute?source-path=/project/'+PROJECT+'&bl=OBSERVED&f.sid=SID&hl=vi&_reqid=700'
        out=fixture('bootstrap',[{'method':'NfrxTb','payload':[14]}],wiz={},entries=[url],at_input='FORM_AT')
        self.assertEqual(len(out['requests']),1)
        self.assertIn('bl=OBSERVED',out['requests'][0]['url'])
        self.assertIn('hl=vi',out['requests'][0]['url'])
        self.assertEqual(out['requests'][0]['form']['at'],'FORM_AT')

    def test_other_project_cannot_supply_missing_context(self):
        url='https://flow.google.com/_/AiSandboxAngularFrontend/data/batchexecute?source-path=/project/other&bl=OTHER'
        out=fixture('bootstrap',[{'method':'NfrxTb','payload':[14]}],wiz={},entries=[url],at_input='FORM_AT')
        self.assertFalse(out['requests'])
        self.assertEqual(out['results'][0]['error'],'session_metadata_missing')

    def test_sequence_increases_when_clock_and_observation_stay_constant(self):
        from urllib.parse import urlsplit,parse_qs
        out=fixture('read',[{'method':'as29s'},{'method':'jwpduf'}])
        ids=[int(parse_qs(urlsplit(x['url']).query)['_reqid'][0])for x in out['requests']]
        self.assertEqual(len(ids),2);self.assertGreater(ids[1],ids[0])

    def test_read_and_bootstrap_ports_cannot_generate(self):
        for scope in ('read','bootstrap'):
            out=fixture(scope,[{'method':'MZZa6b','key':'proof','prepareKey':'VIDEO_GENERATION','prompt':'Wave.'}])
            self.assertFalse(out['requests']);self.assertEqual(out['results'][0]['error'],'method_denied')
        self.assertNotIn('MZZa6b',batch_script('read'))
        self.assertNotIn('maseQ',batch_script('read'))

    def test_generation_cannot_use_upload_verification(self):
        out=fixture('generation',[{'key':'proof','prepareKey':'MEDIA_GENERATION','prompt':'Wave.'}])
        self.assertFalse(out['requests']);self.assertTrue(out['results'][0]['not_sent'])

    def test_oversize_response_is_uncertain_without_retry(self):
        out=fixture('read',[{'method':'as29s'}],response_size=2097153)
        self.assertEqual(len(out['requests']),1)
        self.assertEqual(out['results'][0]['error'],'transport_unconfirmed')


if __name__=='__main__':unittest.main()
