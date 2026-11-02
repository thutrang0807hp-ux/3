"""inspect the observed Flow history step; never import or submit a video."""
import asyncio
import re
from urllib.parse import urlsplit


def normalize(value):
    return re.sub(r'\s+',' ',str(value)).strip()


def route_summary(url):
    """Record route shape, not IDs, query strings, fragments or signed URLs."""
    parsed=urlsplit(url)
    known={'project','edit','editor','media','video','videos','view','viewer','details','asset','assets'}
    parts=[part if part in known else '[id]' for part in parsed.path.split('/') if part]
    return {'origin':parsed.scheme+'://'+(parsed.hostname or ''),'path_shape':'/'+('/'.join(parts))}


def make_detail_check(service,*,page,project_url,account_id,report):
    """Separate inspection guard. Never weakens the sender's assert_ready()."""
    if not isinstance(project_url,str):
        raise RuntimeError('Thiếu URL dự án gốc để kiểm tra trang chi tiết.')
    original=urlsplit(project_url)
    if original.scheme!='https' or original.hostname!='flow.google.com' or not re.fullmatch(r'/project/[a-zA-Z0-9_-]+/?',original.path):
        raise RuntimeError('URL dự án gốc không hợp lệ cho kiểm tra chi tiết.')
    base_path=original.path.rstrip('/')
    session=service.account_session
    binding=dict(service.pinned_binding or {})
    async def check():
        if service.page is not page or page.is_closed() or not service.connected:
            raise RuntimeError('Phiên xem chi tiết đã đổi hoặc đóng.')
        report['detail_route']=route_summary(page.url)
        selection=service.account_bridge.selection()
        if not selection['available'] or selection['account_id']!=account_id:
            raise RuntimeError('Tài khoản được chọn đã đổi; chưa đọc tiếp chi tiết.')
        if service.account_session is not session or service.pinned_binding!=binding:
            raise RuntimeError('Profile hoặc binding đã đổi; chưa đọc tiếp.')
        # This retains the account/profile/session and visible-challenge checks.
        await service.account_bridge.check(session,binding)
        actual=urlsplit(page.url)
        same_origin=(actual.scheme,actual.hostname,actual.port)==(original.scheme,original.hostname,original.port)
        same_project=actual.path.rstrip('/')==base_path or actual.path.startswith(base_path+'/')
        if not same_origin or actual.username or actual.password or not same_project:
            raise RuntimeError('Trang chi tiết chưa xác minh thuộc cùng dự án; xem detail_route.')
    return check


READ_PROMPT = r'''(step,controlledIds)=>{
    const visible=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0};
    const fields=[];
    const add=(method,value)=>{value=String(value||'').trim();if(value)fields.push({method,text:value.slice(0,20000),truncated:value.length>20000})};
    const promptName=/^(prompt|positive prompt|câu lệnh|lời nhắc)\s*:?$/i;
    for(const field of step.querySelectorAll('textarea[readonly],input[readonly],[role="textbox"][aria-readonly="true"]')){
        if(!visible(field))continue;
        const label=field.getAttribute('aria-label')||[...(field.labels||[])].map(e=>e.innerText).join(' ');
        if(promptName.test(label.trim()))add('labelled_readonly_prompt',field.value??field.innerText);
    }
    // An aria-controls relationship explicitly connects Expand prompt to its field.
    for(const id of controlledIds){
        const target=step.ownerDocument.getElementById(id);
        if(!target||['BODY','HTML'].includes(target.tagName)||!visible(target))continue;
        if(target.matches('[contenteditable="true"],textarea:not([readonly]),input:not([readonly])'))continue;
        if(target.querySelector('textarea:not([readonly]),[contenteditable="true"]'))continue;
        add('expand_prompt_aria_controls',target.value??target.innerText);
    }
    const named=[...step.querySelectorAll('button,[role="button"]')].filter(b=>visible(b)&&/^(Expand prompt|Collapse prompt|Mở rộng câu lệnh|Thu gọn câu lệnh|Mở rộng lời nhắc|Thu gọn lời nhắc)$/i.test((b.getAttribute('aria-label')||b.innerText||'').trim()));
    for(const button of named){
        let owner=button.parentElement;
        for(let depth=0;owner&&owner!==step&&depth<4;depth++,owner=owner.parentElement){
            // Do not promote the whole history step to a prompt field.
            if(owner.querySelector('img,video,input,textarea,[contenteditable="true"]'))break;
            const controls=[...owner.querySelectorAll('button,[role="button"],a,[role="menuitem"]')];
            if(controls.some(other=>other!==button))break;
            const clone=owner.cloneNode(true);
            clone.querySelectorAll('button,[role="button"],a,[role="menuitem"],[aria-hidden="true"]').forEach(e=>e.remove());
            add('isolated_expand_prompt_container',clone.textContent);
        }
    }
    return {fields,text_excerpt:(step.innerText||'').slice(0,2500),
        controls:[...step.querySelectorAll('button,[role="button"]')].filter(visible).slice(0,20).map(b=>(b.getAttribute('aria-label')||b.innerText||'').trim().slice(0,160))};
}'''


async def read_history_prompt(page,expected_prompt,check,*,report=None,timeout=5):
    report={} if report is None else report
    report.update(history_found=False,full_prompt_match=False,expand_prompt_clicked=False,
                  request_attribution_confirmed=False,generation_submitted=False,download_started=False)
    await check()
    steps=page.locator('flow-editor-history-step-video').filter(visible=True)
    report['history_step_count']=await steps.count()
    if await steps.count()!=1:
        report['message']='Chưa có duy nhất history step video; chưa chọn hoặc mở rộng prompt.'
        return report
    step=steps.first
    if await step.locator('flow-video-tile').count()!=1:
        report['message']='History step chưa chứa duy nhất flow-video-tile.'
        return report
    report['history_found']=True
    expand=step.get_by_role('button',name=re.compile(r'^\s*(Expand prompt|Mở rộng câu lệnh|Mở rộng lời nhắc)\s*$',re.I)).filter(visible=True)
    ids=[]
    if await expand.count()==1:
        ids=(await expand.get_attribute('aria-controls') or '').split()[:4]
    deadline=asyncio.get_running_loop().time()+timeout
    while True:
        await check()
        data=await step.evaluate(READ_PROMPT,ids)
        report['history_prompt']=data
        exact=[field for field in data['fields'] if not field['truncated'] and normalize(field['text'])==normalize(expected_prompt)]
        if exact:
            report.update(full_prompt_match=True,match_basis=exact[0]['method'],message='Prompt trong history khớp đầy đủ; chưa chứng minh thuộc chính lượt cũ.')
            return report
        if not report['expand_prompt_clicked'] and await expand.count()==1 and await expand.is_enabled():
            await check()
            await expand.click(timeout=3000)
            report['expand_prompt_clicked']=True
        if asyncio.get_running_loop().time()>=deadline:break
        await asyncio.sleep(.2)
    report['message']='Đã đọc history nhưng chưa có trường prompt đầy đủ khớp; không tải hoặc tạo lại video.'
    return report
