"""Offline comparison of reviewed .34/.44 source and supplied Phoma code.

Never launches Phoma or a browser, reads credentials, or sends network requests.
Executes the reviewed Lc payload builder and the two submit transports with
fixture globals and a stubbed fetch. Refuses a different Phoma source hash.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

PHOMA_SHA256 = '929a8acef0f970dbf3bf7672c165119b151cfd6be7f1e8c9c18c88a4084910bd'
UNCHANGED_CHECKS = ('flow_background_session.py', 'flow_account_session.py',
                    'flow_ui_session.py', 'flow_managed_driver.py')


def source(repo, ref, name):
    if ref == 'WORKTREE':
        return (repo / 'veo-node-v46/local_engine' / name).read_bytes()
    result = subprocess.run(['git', 'show', ref + ':veo-node-v46/local_engine/' + name],
                            cwd=repo, capture_output=True)
    if result.returncode:
        raise RuntimeError('git_source_unavailable: ' + ref + ':' + name)
    return result.stdout


def compare(repo, phoma, old_ref='7583a0b', new_ref='48e84aa'):
    raw = phoma.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PHOMA_SHA256:
        raise ValueError('phoma_source_differs_from_reviewed_file')
    code = raw.decode('utf-8')
    files = []
    for name in UNCHANGED_CHECKS:
        old, new = source(repo, old_ref, name), source(repo, new_ref, name)
        files.append({'file': name, 'identical': old == new,
                      'old_sha256': hashlib.sha256(old).hexdigest(),
                      'new_sha256': hashlib.sha256(new).hexdigest()})
    tree = ast.parse(source(repo, new_ref, 'flow_native_reference.py'))
    assignment = next(n for n in tree.body if isinstance(n, ast.Assign) and
                      any(isinstance(t, ast.Name) and t.id == 'SUBMIT' for t in n.targets))
    if isinstance(assignment.value, ast.Constant):
        submit = assignment.value.value
    elif (isinstance(assignment.value, ast.Call) and isinstance(assignment.value.func, ast.Name) and
          assignment.value.func.id == 'batch_script'):
        # Render only our local transport generator, never the Phoma backend.
        namespace = {}
        exec(compile(source(repo,new_ref,'flow_batch_session.py'),'flow_batch_session.py','exec'),namespace)
        submit = namespace['batch_script']('generation')
    else:
        raise ValueError('unsupported_submit_source')
    start = code.index('function Lc(')
    lc = code[start:code.index('function ', start + 15)]
    start = code.index('async function $e(')
    transport = code[start:code.index('async function ', start + 25)]
    project = '11111111-1111-4111-8111-111111111111'
    media = '22222222-2222-4222-8222-222222222222'
    prompt = 'A person waves.\nSame outfit.'
    args = {'key': 'fixtureKey', 'project': project, 'media': media, 'prompt': prompt}
    fixtures = {'project': project, 'media': media, 'prompt': prompt}
    js = '''
const fixture = FIXTURE;
globalThis.window={fixtureKey:{project:fixture.project,token:'FIXTURE_TOKEN',action:'VIDEO_GENERATION',created:1000},
    WIZ_global_data:{cfb2h:'FIXTURE_BUILD',SNlM0e:'FIXTURE_AT',FdrFJe:'FIXTURE_SID'}};
globalThis.location={origin:'https://flow.google.com',pathname:'/project/'+fixture.project};
Object.defineProperty(globalThis,'crypto',{value:{randomUUID:()=> 'FIXTURE_UUID'},configurable:true});
Date.now=()=>1000;let captured;
globalThis.fetch=async(url,options)=>{captured={url:String(url),options};return {status:200,text:async()=> '[]',
    body:{getReader:()=>({read:async()=>({done:true}),cancel:async()=>{}})}}};
const sender=(SENDER);
const we={randomUUID:()=> 'FIXTURE_UUID'};
const Tc=text=>[{text}];
const jo=(p,t)=>[null,22,null,null,null,p,null,null,null,null,[t,1]];
BUILDER
await sender(ARGS);
if(!captured)throw Error('stub_fetch_not_called');
const form=new URLSearchParams(captured.options.body);
const actual=JSON.parse(JSON.parse(form.get('f.req'))[0][0][1]);
const expected=Lc({projectId:fixture.project,prompt:fixture.prompt,modelKey:'veo_3_1_r2v_lite',
    aspectRatio:1,recaptchaToken:'FIXTURE_TOKEN',referenceMedia:[{mediaId:fixture.media}]});
if(JSON.stringify(actual)!==JSON.stringify(expected))throw Error('payload_mismatch');
const scene={
    query_names:[...new URL(captured.url).searchParams.keys()].sort(),
    credentials:captured.options.credentials,explicit_referrer:('referrer' in captured.options),
    header_names:Object.keys(captured.options.headers).sort()};
const Oo='/_/AiSandboxAngularFrontend/data/batchexecute';let c0=0;
const m0=async()=>({buildLabel:'FIXTURE_BUILD',fSid:'FIXTURE_SID',at:'FIXTURE_AT',hl:'en-GB',requestId:1000});
const Pr=()=>[];const fE=()=>null;
TRANSPORT
await $e({evaluate:async(fn,args)=>fn(args)},{rpcId:'MZZa6b',sourcePath:'/project/'+fixture.project,payload:expected});
const phoma={query_names:[...new URL(captured.url).searchParams.keys()].sort(),
    credentials:captured.options.credentials,explicit_referrer:('referrer' in captured.options),
    header_names:Object.keys(captured.options.headers).sort()};
process.stdout.write(JSON.stringify({payload_equal:true,scene_transport:scene,phoma_transport:phoma,
    fixture_scope:'one image, text prompt without reference tags, Lite portrait'}));
'''
    for marker, value in [('FIXTURE', json.dumps(fixtures)), ('SENDER', submit),
                          ('BUILDER', lc), ('TRANSPORT', transport), ('ARGS', json.dumps(args))]:
        # Markers are unique whole placeholders in this script template.
        if marker == 'FIXTURE':
            js = js.replace('const fixture = FIXTURE;', 'const fixture = ' + value + ';')
        elif marker == 'SENDER':
            js = js.replace('(SENDER)', '(' + value + ')')
        elif marker == 'BUILDER':
            js = js.replace('\nBUILDER\n', '\n' + value + '\n')
        elif marker == 'TRANSPORT':
            js = js.replace('\nTRANSPORT\n', '\n' + value + '\n')
        else:
            js = js.replace('sender(ARGS)', 'sender(' + value + ')')
    result = subprocess.run(['node', '--input-type=module', '-e', js], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('offline_payload_comparison_failed: ' + result.stderr[:500])
    return {'old_ref': old_ref, 'new_ref': new_ref, 'phoma_sha256': PHOMA_SHA256,
            'browser_session_sources': files, 'generation_payload': json.loads(result.stdout),
            'network_requests': 0, 'live_generation_verified': False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phoma', type=Path, required=True)
    ap.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument('--output', type=Path)
    ap.add_argument('--new-ref', default='48e84aa', help='Commit or WORKTREE for the code currently being reviewed')
    args = ap.parse_args()
    result = compare(args.repo, args.phoma, new_ref=args.new_ref)
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
