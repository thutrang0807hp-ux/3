"""Tracking diagnostics with an explicit optional thumbnail-open probe.

Never Generate, download, import, retry or mark a historical video as recovered.
"""
import asyncio
import hashlib
import time
from fastapi import HTTPException
from .simple_flow_dom import SNAPSHOT, ResultObserver

async def observer_report(observer, *, include_structure=False):
    page=observer.page
    rows=await page.evaluate(SNAPSHOT,observer.prompt)
    baseline=await page.evaluate('()=>!!window.__sfFlowOldCards')
    candidates=[]
    for row in rows[:40]:
        text=' '.join(str(row.get('text','')).split())
        full=bool(observer.prompt and observer.prompt in text)
        old=row.get('existed') or row['id'] in observer.before
        reasons=[]
        if not baseline:reasons.append('baseline_unavailable')
        if old:reasons.append('existed_before_submit')
        if len(observer.prompt)<8:reasons.append('prompt_too_short')
        if not full:reasons.append('full_prompt_not_in_card')
        if not row.get('activity'):reasons.append('no_supported_activity')
        candidates.append({
            'id':row['id'],'attr':row.get('attr'),'value':row.get('value'),
            'existed':bool(old),'full_prompt_match':full,
            'prefix_match':len(observer.prompt)>=40 and observer.prompt[:40] in text,
            'text_length':len(text),'text_excerpt':text[:500],
            'video':bool(row.get('video')),'failed':bool(row.get('failed')),
            'progress':row.get('progress'),'activity':bool(row.get('activity')),
            'rejected_because':reasons,
            # Deliberately omit signed media URLs.
        })
    inventory=await page.evaluate(r'''()=>{
        const visible=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0};
        const anchors=[...document.querySelectorAll('video,[role="progressbar"],span,[role="status"]')].filter(e=>visible(e)&&(e.matches('video,[role="progressbar"]')||/^\s*\d{1,3}\s*%\s*$/.test(e.innerText||'')));
        return {visible_videos:anchors.filter(e=>e.tagName==='VIDEO').length,
            visible_progressbars:anchors.filter(e=>e.getAttribute('role')==='progressbar').length,
            visible_percent_labels:anchors.filter(e=>!e.matches('video,[role="progressbar"]')).length,
            iframe_count:document.querySelectorAll('iframe').length,
            anchors:anchors.slice(0,12).map(e=>{
                let p=e.parentElement;const parents=[];
                for(let i=0;p&&i<5&&p!==document.body;i++,p=p.parentElement){
                    parents.push({tag:p.tagName.toLowerCase(),role:p.getAttribute('role'),
                        attributes:[...p.attributes].map(a=>a.name).filter(n=>n.startsWith('data-')||n==='id'),
                        text:(p.innerText||'').slice(0,400)});
                }
                return {tag:e.tagName.toLowerCase(),progress:e.getAttribute('aria-valuenow'),parents};
            })};
    }''')
    from .flow_media_structure import collect_media_structure
    structure=await collect_media_structure(page,budget=1.8) if include_structure else None
    return {'checked_at':time.time(),'baseline_available':baseline,
            'observer_card_id':observer.card,'observer_ambiguous':observer.ambiguous,
            'expected_prompt_length':len(observer.prompt),
            'expected_prompt_sha256':hashlib.sha256(observer.prompt.encode()).hexdigest(),
            'expected_prompt_prefix':observer.prompt[:120],
            'total_card_count':len(rows),'cards':candidates,'inventory':inventory,
            'media_structure':structure,'structure_requested':include_structure,
            'read_only':True,'generation_submitted_by_diagnostics':False}

async def inspect_tracking(service,rid,body):
    """Inspect the active page or reopen the saved room project for an old receipt.

    Reopened pages have no reliable before-submit baseline. Report that explicitly;
    never import a video or change the ledger's unknown state on a text match alone.
    """
    record=service.lookup(rid)
    meta=service.ledger.metadata(rid)
    if body.get('store_id')!=service.ledger.store_id or body.get('room_id')!=meta.get('room_id'):
        raise HTTPException(409,'Kho dữ liệu hoặc phòng không khớp lượt đang kiểm tra.')
    prompt=body.get('prompt') or meta.get('prompt')
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>20000:
        raise HTTPException(400,'Thiếu prompt đã gửi của lượt cũ.')
    if not service.account_bridge:raise HTTPException(409,'Cần tài khoản Flow đã chọn.')
    selection=service.account_bridge.selection()
    if not selection['available'] or selection['account_id']!=meta.get('account_id'):
        raise HTTPException(409,'Chọn đúng tài khoản đã gửi lượt này; không tạo lại.')
    async with service.gate:
        if service.busy():
            if service.active!=rid or not service.observer:
                raise HTTPException(409,'Đang có thao tác khác; chưa kiểm tra lượt này.')
            await service.assert_ready()
            snapshot=await asyncio.wait_for(observer_report(service.observer,include_structure=True),5)
            snapshot['session_source']='active_generation'
            if body.get('inspect_video_detail') is True:
                snapshot['video_detail_probe']={'state':'skipped','message':'Lượt còn đang chạy; chưa mở chi tiết làm gián đoạn theo dõi.','generation_submitted':False,'download_started':False,'request_attribution_confirmed':False}
        else:
            if record['state']!='unknown':
                raise HTTPException(409,'Chỉ mở lại dự án để kiểm tra lượt đã gửi nhưng chưa rõ kết quả.')
            pending=getattr(service,'pair_report',None) or {}
            if pending.get('state')=='inputs_sent' and pending.get('generation_ready'):
                raise HTTPException(409,'Đang có ảnh + prompt chưa gửi trong phiên hiện tại; chưa mở lại dự án cũ.')
            # Opening the account's saved project does not submit any generation.
            service.pinned_account=meta['account_id'];service.pinned_room=meta['room_id']
            try:
                if service.page:await service.disconnect_browser()
                await service.restore();await service.assert_ready()
                await service.page.locator('textarea,[contenteditable="true"],[role="textbox"]').first.wait_for(state='visible',timeout=15000)
                observer=ResultObserver(service.page,prompt)
                snapshot=await asyncio.wait_for(observer_report(observer),5)
                deadline=asyncio.get_running_loop().time()+8
                while not snapshot['total_card_count'] and not snapshot['inventory']['visible_videos'] and not snapshot['inventory']['visible_progressbars'] and asyncio.get_running_loop().time()<deadline:
                    await asyncio.sleep(1);await service.assert_ready()
                    snapshot=await asyncio.wait_for(observer_report(observer),5)
                # Heavy structural scan once, after the ordinary load checks.
                snapshot=await asyncio.wait_for(observer_report(observer,include_structure=True),5)
                if body.get('inspect_video_detail') is True:
                    from .flow_video_detail_probe import inspect_video_details
                    from .flow_media_structure import collect_media_structure
                    probe={}
                    try:
                        await asyncio.wait_for(inspect_video_details(service.page,prompt,service.assert_ready,report=probe),20)
                    except asyncio.TimeoutError:
                        probe.update(state='needs_inspection',message='Hết thời gian đọc chi tiết; không tạo lại hoặc tải video.')
                    snapshot['video_detail_probe']=probe
                    snapshot['read_only']=not probe.get('thumbnail_clicked',False)
                    snapshot['media_structure_after_detail']=await collect_media_structure(service.page,budget=1.8)
                snapshot['session_source']='reopened_for_read_only_inspection'
                snapshot['baseline_available']=False
                for card in snapshot['cards']:
                    if 'baseline_unavailable' not in card['rejected_because']:
                        card['rejected_because'].append('baseline_unavailable')
            finally:
                await service.disconnect_browser()
        service.ledger.set_metadata(rid,{'result_tracking':snapshot})
        return {**service.diagnose(rid,body['store_id'],body['room_id']),
                'result_tracking':snapshot,'message':'Đã thu thập báo cáo cấu trúc/chi tiết video; chưa nhận hoặc xác nhận video, không gửi lượt tạo mới.'}
