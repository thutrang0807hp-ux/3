"""Open one observed Flow video thumbnail and inspect its details.

Never Generate, Reuse prompt, download, retry, or change a request state.
A matching prompt alone does not prove which historical request produced a video.
"""
import asyncio
import hashlib
import re
import secrets


def normalize(value):
    return re.sub(r'\s+',' ',str(value)).strip()


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


async def video_candidates(page):
    candidates=[]
    # These tags and img.thumbnail were observed in the user's .37 report.
    tiles=page.locator('flow-grid-tile-container').filter(
        has=page.locator('flow-video-tile')
    ).filter(visible=True)
    if await tiles.count()>20:raise RuntimeError('Quá nhiều thẻ video để kiểm tra duy nhất; chưa click.')
    for tile in (await tiles.all())[:20]:
        thumbnail=tile.locator('flow-video-tile img.thumbnail').filter(visible=True)
        if await thumbnail.count()!=1:continue
        source=await thumbnail.evaluate('e=>e.currentSrc||e.src')
        if not source:continue
        token=secrets.token_hex(12)
        await tile.evaluate('(e,token)=>e.setAttribute("data-sf-video-probe",token)',token)
        candidates.append({'token':token,'label':(await tile.get_attribute('aria-label') or '')[:240],
                           'thumbnail_source_sha256':digest(source)})
    return candidates


async def read_new_detail(page,marker,expected):
    """Inspect newly displayed video containers, not the page/composer as a whole.

    Region rules here are discovery heuristics. Their actual applicability to
    Flow's video-detail view has not yet been verified on the user's account.
    """
    videos=page.locator('video').filter(visible=True)
    regions=[];probes=[]
    for video in (await videos.all())[:10]:
        if await video.get_attribute(marker)=='visible':continue
        for depth in range(1,9):
            area=video.locator('xpath=ancestor::*['+str(depth)+']')
            if await area.count()!=1:break
            probe=await area.evaluate(r'''e=>{
                const visible=x=>{const r=x.getBoundingClientRect();return r.width>0&&r.height>0};
                const tag=e.tagName.toLowerCase(),position=getComputedStyle(e).position;
                const role=e.getAttribute('role');
                const count=[...e.querySelectorAll('video')].filter(visible).length;
                const editor=[...e.querySelectorAll('textarea:not([readonly]):not([disabled]),[contenteditable="true"]')].some(visible);
                const close=[...e.querySelectorAll('button,[role="button"]')].filter(visible).some(b=>/^(close|dismiss|đóng|close preview|close video|×|✕)$/i.test((b.getAttribute('aria-label')||b.innerText||'').trim()));
                const boundary=['body','html'].includes(tag);
                const detail=role==='dialog'||(/^flow-/.test(tag)&&/detail|viewer|preview/.test(tag))||(['fixed','absolute'].includes(position)&&close);
                return {tag,role,position,video_count:count,editor,close,boundary,qualified:!boundary&&count===1&&!editor&&detail};
            }''')
            probes.append(probe)
            if probe['boundary']:break
            if not probe['qualified']:continue
            key=await area.get_attribute('data-sf-detail-probe')
            if not key:
                key=secrets.token_hex(12)
                await area.evaluate('(e,key)=>e.setAttribute("data-sf-detail-probe",key)',key)
            if key not in [item[0] for item in regions]:regions.append((key,area))
            break
    if len(regions)!=1:
        return {'detail_found':False,'qualified_region_count':len(regions),'region_probes':probes}
    _,area=regions[0]
    data=await area.evaluate(r'''e=>{
        const visible=x=>{const r=x.getBoundingClientRect();return r.width>0&&r.height>0};
        const promptName=/^(prompt|positive prompt|câu lệnh|lời nhắc)\s*:?$/i;
        const fields=[];
        const add=(method,label,value)=>{value=String(value||'').trim();if(value)fields.push({method,label:label.slice(0,160),text:value.slice(0,20000),truncated:value.length>20000})};
        for(const field of e.querySelectorAll('textarea[readonly],input[readonly],[role="textbox"][aria-readonly="true"]')){
            if(!visible(field))continue;
            const label=field.getAttribute('aria-label')||[...(field.labels||[])].map(l=>l.innerText).join(' ');
            if(promptName.test(label.trim()))add('labelled_readonly_field',label,field.value??field.innerText);
        }
        for(const label of e.querySelectorAll('label,dt')){
            if(!visible(label)||!promptName.test((label.innerText||'').trim()))continue;
            const field=label.nextElementSibling;
            if(field&&visible(field))add('labelled_adjacent_field',label.innerText,field.value??field.innerText);
        }
        return {tag:e.tagName.toLowerCase(),fields,
            // Bounded diagnostic text, never used by itself to confirm a prompt.
            text_excerpt:(e.innerText||'').slice(0,2500),
            controls:[...e.querySelectorAll('button,[role="button"],a')].filter(visible).slice(0,20).map(b=>({tag:b.tagName.toLowerCase(),name:(b.getAttribute('aria-label')||b.innerText||'').trim().slice(0,160)}))};
    }''')
    exact=[field for field in data['fields'] if not field['truncated'] and normalize(field['text'])==normalize(expected)]
    return {'detail_found':True,'qualified_region_count':1,'region_probes':probes,
            'detail':data,'full_prompt_match':bool(exact),
            'match_basis':'labelled_full_prompt' if exact else None}


async def inspect_video_details(page,expected_prompt,check,*,report=None,detail_timeout=10,detail_check=None):
    report={} if report is None else report
    report.update(state='inspecting',thumbnail_clicked=False,detail_found=False,
                  full_prompt_match=False,request_attribution_confirmed=False,
                  generation_submitted=False,download_started=False,logs=[])
    def log(text):report['logs'].append(text)
    if not isinstance(expected_prompt,str) or not expected_prompt.strip() or len(expected_prompt)>20000:
        raise ValueError('Cần prompt gốc của lượt đã gửi, tối đa 20.000 ký tự.')
    report['expected_prompt_sha256']=digest(normalize(expected_prompt))
    before_marker='data-sf-before-video-'+secrets.token_hex(8)
    try:
        await check()
        # Leave any existing video viewer alone.
        if await page.locator('video').filter(visible=True).count():
            report.update(state='needs_inspection',message='Đang có video mở sẵn; chưa click thumbnail khác.')
            return report
        report['visible_video_tile_count']=await page.locator('flow-grid-tile-container').filter(has=page.locator('flow-video-tile')).filter(visible=True).count()
        candidates=await video_candidates(page)
        report['candidates']=candidates
        if report['visible_video_tile_count']!=1 or len(candidates)!=1:
            report.update(state='needs_inspection',message='Không có duy nhất thumbnail video trong vùng đang hiển thị; chưa mở hoặc chọn đại.')
            return report
        chosen=candidates[0]
        tile=page.locator('[data-sf-video-probe="'+chosen['token']+'"]')
        thumbnail=tile.locator('flow-video-tile img.thumbnail').filter(visible=True)
        await check()
        if await tile.count()!=1 or await thumbnail.count()!=1:
            raise RuntimeError('Thẻ video đã thay đổi trước khi mở chi tiết.')
        source=await thumbnail.evaluate('e=>e.currentSrc||e.src')
        if digest(source)!=chosen['thumbnail_source_sha256']:
            raise RuntimeError('Thumbnail đã đổi trước khi mở; chưa click.')
        # Only the observed thumbnail is clicked. Never its Reuse prompt button.
        await page.locator('video').evaluate_all('(xs,key)=>xs.forEach(e=>{const r=e.getBoundingClientRect();e.setAttribute(key,r.width>0&&r.height>0?"visible":"hidden")})',before_marker)
        await thumbnail.click(timeout=4000)
        report['thumbnail_clicked']=True
        log('Đã click thumbnail của duy nhất thẻ video để đọc chi tiết; chưa xác nhận thuộc lượt cũ.')
        deadline=asyncio.get_running_loop().time()+detail_timeout
        while asyncio.get_running_loop().time()<deadline:
            await (detail_check or check)()
            from .flow_video_history import read_history_prompt
            if await page.locator('flow-editor-history-step-video').filter(visible=True).count():
                result=await read_history_prompt(page,expected_prompt,detail_check or check,timeout=5)
                report.update(result)
                report['detail_found']=bool(result.get('history_found'))
                break
            result=await asyncio.wait_for(read_new_detail(page,before_marker,expected_prompt),timeout=2)
            report.update(result)
            if result.get('full_prompt_match'):break
            await asyncio.sleep(.25)
        report['state']='details_read' if report['detail_found'] else 'needs_inspection'
        report['message']='Đã đọc prompt đầy đủ và khớp; chưa chứng minh thuộc đúng lượt cũ.' if report['full_prompt_match'] else 'Chưa đọc được prompt đầy đủ khớp trong vùng chi tiết; không tải hoặc tạo lại video.'
        log(report['message'])
    except asyncio.CancelledError:
        report.update(state='cancelled',message='Đã dừng đọc chi tiết, không gửi tạo hoặc tải video.')
        raise
    except Exception as exc:
        report.update(state='needs_inspection',error_type=type(exc).__name__,
                      message='Chưa mở/đọc được chi tiết; giữ nguyên lượt cũ, không tạo lại.')
    finally:
        # Keep the viewer open for inspection; do not guess its Close button.
        try:
            await page.locator('['+before_marker+']').evaluate_all('(xs,key)=>xs.forEach(e=>e.removeAttribute(key))',before_marker)
            await page.locator('[data-sf-video-probe]').evaluate_all('xs=>xs.forEach(e=>e.removeAttribute("data-sf-video-probe"))')
            await page.locator('[data-sf-detail-probe]').evaluate_all('xs=>xs.forEach(e=>e.removeAttribute("data-sf-detail-probe"))')
        except Exception:pass
        report.update(generation_submitted=False,download_started=False,request_attribution_confirmed=False)
    return report
