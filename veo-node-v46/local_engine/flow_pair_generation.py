"""Validate a successful direct-composer receipt before one video submission.

Uses the existing request ledger, single-click sender and ResultObserver.
No generation is performed by these validation helpers.
"""
import hashlib
import json
import re
from .flow_prepare import PrepareStopped,reference_scope,editor_text
from .flow_settings import DEFAULTS,settings_panel,read_settings


def normalized_prompt(value):
    return re.sub(r'\s+',' ',str(value)).strip()


async def composer_fingerprint(page):
    """Detect changes since the successful upload; no screenshot/pixel matching."""
    _,scope=await reference_scope(page)
    if scope is None:return None
    images=await scope.locator('img').evaluate_all('''xs=>xs.filter(e=>{const r=e.getBoundingClientRect();return r.width>=20&&r.height>=20}).map(e=>{
        const p=e.closest('[data-media-id],[data-asset-id]');
        return {src:e.currentSrc||e.src,id:p&&(p.getAttribute('data-media-id')||p.getAttribute('data-asset-id'))};
    })''')
    if len(images)!=1 or not images[0]['src']:return None
    return hashlib.sha256(json.dumps(images,sort_keys=True).encode()).hexdigest()


async def seal_pair(service,report,settings):
    report['settings']=dict(settings)
    report['generation_ready']=False
    if not all(report.get(key) for key in ('delivered','image_attached','prompt_filled','prompt_verified','settings_verified')):return
    fingerprint=await composer_fingerprint(service.page)
    if not fingerprint:
        report.setdefault('logs',[]).append('Chưa ghi nhận duy nhất ảnh trong composer để mở nút tạo.')
        return
    report['composer_fingerprint']=fingerprint
    report['generation_ready']=settings==DEFAULTS
    # Existing one-click sender marks this receipt submitted after final validation.
    service.prepare_report=report


async def validate_pair(service,payload,raw):
    report=getattr(service,'pair_report',None)
    if not report or payload.get('prepared_request_id')!=report.get('request_id'):
        raise PrepareStopped('Không có lượt ảnh + prompt tương ứng.')
    expected_state='cli_inputs_ready' if report.get('preparation_method')=='cli_reference_pipeline' else 'inputs_sent'
    if report.get('state')!=expected_state or not report.get('generation_ready'):
        raise PrepareStopped('Lượt ảnh + prompt chưa sẵn sàng hoặc đã được dùng để tạo.')
    for key in ('room_id','scene_id','part','account_id'):
        if payload.get(key)!=report.get(key):raise PrepareStopped('Lượt chuẩn bị thuộc cảnh hoặc tài khoản khác.')
    selection=service.account_bridge.selection()
    if not selection['available'] or selection['account_id']!=report['account_id']:
        raise PrepareStopped('Tài khoản Flow đã thay đổi; chưa tạo video.')
    if service.page is not service.pair_page or service.page.is_closed():
        raise PrepareStopped('Phiên Flow đã thay đổi; chuẩn bị lại ảnh và prompt.')
    if hashlib.sha256(raw).hexdigest()!=report['reference_sha256']:
        raise PrepareStopped('Ảnh nguồn đã đổi sau khi chuẩn bị.')
    if hashlib.sha256(payload['prompt'].strip().encode()).hexdigest()!=report['prompt_sha256']:
        raise PrepareStopped('Prompt đã đổi sau khi chuẩn bị.')
    await service.assert_ready()
    if report.get('preparation_method')=='cli_reference_pipeline':
        from .flow_video_options import request_settings
        if request_settings(payload)!=report.get('settings'):raise PrepareStopped('Cấu hình đã đổi sau chuẩn bị; chưa gửi tạo.')
    if report.get('preparation_method') in ('native_reference_pipeline','cli_reference_pipeline'):
        from .flow_native_pipeline import validate_receipt,NativePipelineStopped
        try:await validate_receipt(service,report)
        except NativePipelineStopped as exc:raise PrepareStopped(str(exc))from None
        return
    panel=await settings_panel(service.page)
    try:actual=await read_settings(panel)
    finally:await service.page.keyboard.press('Escape')
    if actual!=DEFAULTS or report.get('settings')!=DEFAULTS:
        raise PrepareStopped('Cần Ingredients · Lite · 9:16 · x1 trước khi tạo.')
    editor,_=await reference_scope(service.page)
    if editor is None or normalized_prompt(await editor_text(editor))!=normalized_prompt(payload['prompt']):
        raise PrepareStopped('Prompt trên Flow đã đổi; chưa tạo video.')
    fingerprint=await composer_fingerprint(service.page)
    if not fingerprint or fingerprint!=report.get('composer_fingerprint'):
        raise PrepareStopped('Ảnh trong composer đã đổi; chưa tạo video.')
