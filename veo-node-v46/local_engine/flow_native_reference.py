"""Experimental native-session reference submit. Never retries or clicks Generate.

Uses only the page's normal Enterprise API. No Phoma preload/hijack, fingerprint
patch, challenge solver, alternate profile, or credential export is included.
"""
import asyncio
from .flow_batch_session import batch_script, CONTEXT_JS
import base64
import hashlib
import json
import secrets
from urllib.parse import parse_qs
from .flow_task_protocol import UUID, project_from_url, batch_endpoint, rpc_payload
from .flow_prepare import reference_scope


class DirectNotReady(RuntimeError):
    pass


class UploadMediaCapture:
    """Resolve only an upload whose project AND original image bytes match.

    Passive observation around the existing uploader. No new upload request.
    Unsupported/ambiguous response shapes leave the ID unresolved.
    """
    def __init__(self, page, image, report):
        self.page, self.report = page, report
        self.project = project_from_url(page.url)
        self.digest = hashlib.sha256(image.read_bytes()).hexdigest()
        self.requests, self.tasks, self.ids = set(), set(), set()

    def start(self):
        self.page.on('request', self.request)
        self.page.on('response', self.response)

    def request(self, request):
        try:
            if len(self.requests) >= 4 or request.method != 'POST' or not batch_endpoint(request.url):
                return
            raw = request.post_data
            if not isinstance(raw, str) or len(raw) > 10 * 1024**2:
                return
            fields = parse_qs(raw, max_num_fields=40)
            envelopes = fields.get('f.req', [])
            if len(envelopes) != 1:
                return
            outer = json.loads(envelopes[0])
            if len(outer) != 1 or len(outer[0]) != 1:
                return
            call = outer[0][0]
            if call[0] != 'maseQ':
                return
            payload = json.loads(call[1])
            if payload[0][5] != self.project or not isinstance(payload[1], str):
                return
            image = base64.b64decode(payload[1], validate=True)
            if hashlib.sha256(image).hexdigest() == self.digest:
                self.requests.add(request)
        except (ValueError, TypeError, IndexError, KeyError, RecursionError):
            return

    def response(self, response):
        if response.request not in self.requests or not 200 <= response.status < 300:
            return
        task = asyncio.create_task(self.read(response))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def read(self, response):
        try:
            raw = await asyncio.wait_for(response.body(), 3)
            if len(raw) > 2 * 1024**2:
                return
            payload = rpc_payload(raw, 'maseQ')
            ids = set()
            budget = 512
            def walk(value, depth=0):
                nonlocal budget
                budget -= 1
                if budget < 0 or depth > 12:
                    raise ValueError('upload_response_limit')
                if isinstance(value, str) and UUID.fullmatch(value) and value != self.project:
                    ids.add(value)
                elif isinstance(value, list):
                    for child in value:
                        walk(child, depth + 1)
            walk(payload)
            # Do not pick the first arbitrary UUID in an unsupported response.
            if len(ids) == 1:
                self.ids.update(ids)
                if len(self.ids) == 1:
                    self.report.update(uploaded_media_id=next(iter(self.ids)),
                        uploaded_media_project=self.project, uploaded_media_source_sha256=self.digest,
                        uploaded_media_evidence='matching_upload_bytes_and_unique_response_id')
                else:
                    self.report.pop('uploaded_media_id', None)
                    self.report['uploaded_media_evidence'] = 'ambiguous_upload_ids'
        except Exception:
            # Never export upload bodies, native request context or error text.
            self.report['uploaded_media_capture_error'] = 'unsupported_upload_response'

    async def close(self):
        self.page.remove_listener('request', self.request)
        self.page.remove_listener('response', self.response)
        if self.tasks:
            tasks = list(self.tasks)
            _, pending = await asyncio.wait(tasks, timeout=3)
            for task in pending:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


async def attached_reference(page, report):
    _, scope = await reference_scope(page)
    if scope is None:
        raise DirectNotReady('Chưa xác định được composer; chưa gửi tạo.')
    records = await scope.locator('img').evaluate_all('''xs => xs.filter(e => {
        const r=e.getBoundingClientRect(); return r.width>=20 && r.height>=20;
    }).map(e => { const p=e.closest('[data-media-id],[data-asset-id]');
        return p && (p.getAttribute('data-media-id') || p.getAttribute('data-asset-id'));
    })''')
    if len(records) != 1:
        raise DirectNotReady('Cần đúng một ảnh trong composer; chưa gửi tạo.')
    media = records[0]
    # A sealed preparation receipt may provide an ID resolved from that upload.
    if not media:
        media = report.get('uploaded_media_id')
    if not isinstance(media, str) or not UUID.fullmatch(media):
        raise DirectNotReady('Ảnh đã gắn nhưng chưa đọc được mediaId nguồn. Chưa gửi tạo; không đoán ID từ thumbnail.')
    if report.get('uploaded_media_id') and report['uploaded_media_id'] != media:
        raise DirectNotReady('ID ảnh khác lượt chuẩn bị; chưa gửi tạo.')
    if report.get('uploaded_media_project') and report['uploaded_media_project'] != project_from_url(page.url):
        raise DirectNotReady('ID ảnh thuộc dự án khác; chưa gửi tạo.')
    if report.get('uploaded_media_source_sha256') and report['uploaded_media_source_sha256'] != report.get('reference_sha256'):
        raise DirectNotReady('ID ảnh không khớp nguồn đã chuẩn bị; chưa gửi tạo.')
    return media


PREFLIGHT = (r'''async ({key,project,action='VIDEO_GENERATION'}) => {
''' + CONTEXT_JS + r'''
    if(!['VIDEO_GENERATION','MEDIA_GENERATION'].includes(action)) return {error:'native_action_denied'};
    const projectPath='/project/'+project;
    const current=()=>location.origin==='https://flow.google.com' &&
        location.pathname.replace(/\/$/,'')===projectPath;
    if(!current()) return {error:'project_changed'};
    const ctx=contextFor(project,true);
    if(ctx.error)return {error:ctx.error};
    const keys=new Set([...document.querySelectorAll('script[src]')].flatMap(e=>{
        try{const u=new URL(e.src);const host=u.hostname;
            if(!['www.google.com','www.recaptcha.net'].includes(host) ||
               !u.pathname.endsWith('/recaptcha/enterprise.js')) return [];
            const k=u.searchParams.get('render');return k&&k!=='explicit'?[k]:[];
        }catch{return [];}
    }));
    for(const e of document.querySelectorAll('[data-sitekey]')){
        const k=e.getAttribute('data-sitekey');if(k)keys.add(k);
    }
    if(keys.size!==1) return {error:'native_sitekey_not_unique'};
    const api=window.grecaptcha?.enterprise;
    if(!api || typeof api.ready!=='function' || typeof api.execute!=='function')
        return {error:'native_enterprise_unavailable'};
    let timer;
    try{
        const token=await Promise.race([
            new Promise((resolve,reject)=>api.ready(()=>{
                Promise.resolve().then(()=>api.execute([...keys][0],{action})).then(resolve,reject);
            })),
            new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('timeout')),10000);})
        ]);
        if(!current() || typeof token!=='string' || !token) return {error:'native_verification_failed'};
        window[key]={project,token,action,created:Date.now()};
        return {ready:true};
    }catch{return {error:'native_verification_failed'};}
    finally{clearTimeout(timer);}
}'''
)


SUBMIT = batch_script('generation')


async def prepare(service, report):
    await service.assert_ready()
    project = project_from_url(service.page.url)
    if project != project_from_url(service.project):
        raise DirectNotReady('Dự án Flow đã đổi; chưa gửi tạo.')
    if report.get('preparation_method') == 'native_reference_pipeline':
        media = report.get('uploaded_media_id')
        if (not report.get('reference_verified') or not isinstance(media, str) or
            not UUID.fullmatch(media) or report.get('uploaded_media_project') != project):
            raise DirectNotReady('Lượt upload trực tiếp chưa có ID ảnh đã xác minh; chưa gửi tạo.')
    else:
        media = await attached_reference(service.page, report)
    key = '__sfNativeReference_' + secrets.token_hex(12)
    result = await asyncio.wait_for(service.page.evaluate(PREFLIGHT, {'key': key, 'project': project}), 12)
    if not isinstance(result, dict) or result.get('ready') is not True:
        code = result.get('error', 'preflight_failed') if isinstance(result, dict) else 'preflight_failed'
        raise DirectNotReady('Phiên Flow chưa sẵn sàng gửi trực tiếp ('+code+'). Chưa gửi tạo; không tự chuyển sang bấm Generate.')
    return {'key': key, 'project': project, 'media': media}


async def discard(page, prepared):
    try:
        await page.evaluate('(key)=>{delete window[key]}', prepared['key'])
    except Exception:
        pass


async def submit(service, rid, payload, prepared, tracker):
    await service.assert_ready()
    tracker.mark_generate_attempt()
    tracker.bind_direct_request(prepared['media'])
    # Only the existing RequestLedger owns dispatch. No second SceneStore claim.
    metadata={'clicked':False,'direct_rpc_attempted':True,'submission_method':'native_reference_rpc'}
    report=getattr(service,'pair_report',None)
    if report and report.get('preparation_method')=='native_reference_pipeline':
        report.update(native_stage='generation_dispatching',generation_submitted=None,generation_ready=False,
                      message='Đã bắt đầu lệnh gửi tạo; đang chờ Flow xác nhận.')
        metadata['native_inputs']=dict(report)
    service.ledger.set_metadata(rid, metadata)
    service.sent = True  # Set before the browser call: cancellation is ambiguous.
    reply = await asyncio.wait_for(service.page.evaluate(SUBMIT, {
        **prepared, 'prompt': payload['prompt']}), 25)
    if not isinstance(reply, dict):
        raise DirectNotReady('Chưa xác định phản hồi gửi tạo; giữ lượt, không tự gửi lại.')
    if reply.get('not_sent') is True:
        service.sent = False
        if report and report.get('preparation_method')=='native_reference_pipeline':
            report.update(native_stage='generation_not_sent',generation_submitted=False,generation_ready=False,
                          message='Phiên thay đổi hoặc hết hạn trước lệnh gửi; chưa tạo video.')
            service.ledger.set_metadata(rid,{'native_inputs':dict(report),'direct_rpc_not_sent':True})
        raise DirectNotReady('Phiên chuẩn bị đã hết hạn trước lệnh gửi; chưa tạo video.')
    status = reply.get('status')
    if type(status) is not int or not isinstance(reply.get('body'), str):
        raise DirectNotReady('Đã bắt đầu lệnh gửi nhưng chưa nhận đủ phản hồi. Giữ lượt để kiểm tra; không tự gửi lại.')
    tracker.accept_direct_response(status, reply['body'])
    metadata={'direct_rpc_response_received':True}
    if report and report.get('preparation_method')=='native_reference_pipeline':
        rejected=tracker.snapshot()['state']=='rpc_rejected'
        report.update(native_stage='generation_accepted' if tracker.identity else 'generation_rejected' if rejected else 'generation_unconfirmed',
                      generation_submitted=True if tracker.identity else False if rejected else None,
                      generation_ready=False,message='Flow đã trả ID video; đang theo dõi.' if tracker.identity else
                      'Flow đã từ chối lệnh tạo; không tự gửi lại.' if rejected else
                      'Chưa xác nhận Flow tiếp nhận; giữ lượt để kiểm tra, không tự gửi lại.')
        metadata['native_inputs']=dict(report)
    service.ledger.set_metadata(rid, metadata)
