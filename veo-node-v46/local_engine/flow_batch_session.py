"""One normal same-origin Flow batch transport, with per-scope method ACLs.

Metadata stays in the page. No credentials, challenge tokens or signed URLs are
exported through this context reader. This does not modify verification APIs,
browser identity, challenge scripts or profile data.
"""
import json


CONTEXT_JS = r'''
function contextFor(project, requireAt=true) {
    const path=project?'/project/'+project:'/';
    if(location.origin!=='https://flow.google.com' ||
       (project?location.pathname.replace(/\/$/,'')!==path:location.pathname!=='/'))
        return {error:'project_changed'};
    const scalar=value=>typeof value==='string'||typeof value==='number'?String(value):'';
    const wiz=window.WIZ_global_data || {};
    const batchPath='/_/AiSandboxAngularFrontend/data/batchexecute';
    let previous=null;
    for(const item of performance.getEntriesByType('resource')) {
        try {
            const url=new URL(item.name,location.origin);
            if(url.origin===location.origin && url.pathname===batchPath &&
               url.searchParams.get('source-path')===path)previous=url;
        } catch {}
    }
    const params=previous?.searchParams || new URLSearchParams();
    const build=scalar(wiz.cfb2h)||params.get('bl')||'';
    const sid=scalar(wiz.FdrFJe)||params.get('f.sid')||'';
    const at=scalar(wiz.SNlM0e)||document.querySelector('input[name="at"]')?.value?.trim()||
        document.querySelector('meta[name="at"],meta[property="at"]')?.content?.trim()||'';
    if(!build || (requireAt&&!at))return {error:'session_metadata_missing'};
    const hl=params.get('hl')||'en-GB';
    const rawId=params.get('_reqid')||'';
    const base=/^\d{1,12}$/.test(rawId)?Number(rawId):Math.floor(Date.now()%100000000);
    return {path,build,sid,at,hl,base,batchPath};
}
'''

_BOOTSTRAP_PAYLOAD = r'''
if(method==='maseQ') {
    const state=window[key];delete window[key];
    if(!state || state.project!==project || state.action!=='MEDIA_GENERATION' ||
       Date.now()-state.created>20000 || !upload || typeof upload.base64!=='string' ||
       !['image/png','image/jpeg','image/webp'].includes(upload.mime))
        return {not_sent:true,error:'upload_session_expired'};
    const id=()=>crypto.randomUUID().toUpperCase();
    payload=[[null,22,null,null,null,project,null,null,null,null,[state.token,1]],
        upload.base64,upload.mime,1,null,null,null,null,upload.filename,null,id(),id()];
} else if(upload || key) return {not_sent:true,error:'unexpected_upload_arguments'};
'''

_GENERATION_PAYLOAD = r'''
const state=window[key];delete window[key];
if(!state || state.project!==project || state.action!=='VIDEO_GENERATION' ||
   Date.now()-state.created>20000 || typeof prompt!=='string' || !prompt.trim() ||
   typeof media!=='string')return {not_sent:true,error:'prepared_session_expired'};
const id=()=>crypto.randomUUID().toUpperCase();
payload=[[[[null,null,[[[prompt]]]],[[null,media]],'veo_3_1_r2v_lite',1,null,
    [null,null,null,null,id(),id()]]],
    [null,22,null,null,null,project,null,null,null,null,[state.token,1]],[id(),2]];
'''

_READ_PAYLOAD = r'''
if(batchPath && batchPath!==ctx.batchPath)return {not_sent:true,error:'read_endpoint_denied'};
if(upload || key)return {not_sent:true,error:'unexpected_read_arguments'};
payload=method==='jwpduf'?[null,null,[[media]]]:[media];
'''


def batch_script(scope):
    """Compile ACL and payload code into the script, not caller-selected scope.

    The read script contains no generation or upload implementation. All three
    scopes share metadata, sequence, referrer, cookie and response handling.
    """
    if scope == 'bootstrap':
        allowed = ('jHPbke', 'NfrxTb', 've2Lsc', 'DTaVef', 'nzlxg', 'maseQ', 'as29s')
        payload_code, timeout, default_method = _BOOTSTRAP_PAYLOAD, 30000, None
    elif scope == 'generation':
        allowed = ('MZZa6b',)
        payload_code, timeout, default_method = _GENERATION_PAYLOAD, 20000, 'MZZa6b'
    elif scope == 'read':
        allowed = ('jwpduf', 'as29s')
        payload_code, timeout, default_method = _READ_PAYLOAD, 8000, None
    else:
        raise ValueError('batch_scope_invalid')
    opening = 'async ({method=' + json.dumps(default_method) + ',project,payload,key=null,upload=null,media,prompt,batchPath}) => {\n'
    acl = '''
const allowed=ALLOWED;
if(!allowed.includes(method))return {not_sent:true,error:'method_denied'};
if(!project && method!=='jHPbke')return {not_sent:true,error:'project_required'};
const ctx=contextFor(project,REQUIRE_AT);
if(ctx.error)return {not_sent:true,error:ctx.error};
'''.replace('ALLOWED', json.dumps(allowed)).replace('REQUIRE_AT', 'false' if scope == 'read' else 'true')
    # Avoid including the project-creation method in the read scope at all.
    if scope != 'bootstrap':
        acl = acl.replace("if(!project && method!=='jHPbke')", 'if(!project)')
    transport = r'''
const endpoint=new URL(ctx.batchPath,location.origin);
endpoint.searchParams.set('rpcids',method);endpoint.searchParams.set('source-path',ctx.path);
endpoint.searchParams.set('bl',ctx.build);if(ctx.sid)endpoint.searchParams.set('f.sid',ctx.sid);
endpoint.searchParams.set('hl',ctx.hl);endpoint.searchParams.set('rt','c');
const sequences=window.__sfFlowBatchSequence || (window.__sfFlowBatchSequence=Object.create(null));
const prior=sequences[ctx.path] || {sequence:0,last:0};
const sequence=Number.isSafeInteger(prior.sequence)?prior.sequence+1:1;
const last=Number.isSafeInteger(prior.last)?prior.last:0;
const requestId=Math.max(ctx.base+100000+(sequence%10000),last+1);
sequences[ctx.path]={sequence,last:requestId};
endpoint.searchParams.set('_reqid',String(requestId));
const form=new URLSearchParams();form.set('f.req',JSON.stringify([[[method,JSON.stringify(payload),null,'generic']]]));
if(ctx.at)form.set('at',ctx.at);
const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),TIMEOUT);
try {
    const response=await fetch(endpoint,{method:'POST',credentials:'include',redirect:'error',
        referrer:new URL(ctx.path,location.origin).href,
        headers:{'content-type':'application/x-www-form-urlencoded;charset=UTF-8','x-same-domain':'1'},
        body:form,signal:controller.signal});
    if(!response.body)return {status:response.status,error:'response_body_missing'};
    const reader=response.body.getReader(),chunks=[];let size=0;
    try {
        while(true) {
            const {done,value}=await reader.read();if(done)break;
            size+=value.length;if(size>2097152)throw Error('response_limit');chunks.push(value);
        }
    } finally { await reader.cancel().catch(()=>{}); }
    const bytes=new Uint8Array(size);let offset=0;
    for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
    return {status:response.status,body:new TextDecoder('utf-8',{fatal:true}).decode(bytes)};
} catch { return {error:'transport_unconfirmed'}; }
finally { clearTimeout(timer);controller.abort(); }
'''.replace('TIMEOUT', str(timeout))
    return opening + CONTEXT_JS + acl + payload_code + transport + '\n}'
