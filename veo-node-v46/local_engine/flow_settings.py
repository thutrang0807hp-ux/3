"""Apply composer settings through visible Flow controls, without submitting media."""
import asyncio
import copy
import hashlib
import json
import re
import secrets

from fastapi import HTTPException
from fastapi.responses import FileResponse


class SettingsUnavailable(RuntimeError):
    pass


DEFAULTS = {'kind': 'video', 'mode': 'ingredients', 'ratio': '9:16', 'model': 'lite', 'outputs': 1}
ALLOWED = {'kind': ('video',), 'mode': ('frames', 'ingredients'),
           'ratio': ('16:9', '9:16'), 'model': ('lite', 'fast', 'quality'), 'outputs': (1, 2, 3, 4)}
LABELS = {'kind': {'video': r'(?:videocam\s*)?(?:Video)', 'image': r'(?:image\s*)?(?:Image|Hình ảnh)'},
          'mode': {'frames': r'(?:crop_free\s*)?(?:Frames|Khung hình)',
                   'ingredients': r'(?:category\s*)?(?:Ingredients|Thành phần)'},
          'ratio': {'16:9': r'(?:crop_landscape\s*)?16\s*:\s*9',
                    '9:16': r'(?:crop_portrait\s*)?9\s*:\s*16'},
          'outputs': {i: rf'x\s*{i}' for i in range(1, 5)},
          'model': {m: rf'Veo\s*3\.1\s*[-·–]?\s*{m}(?:\s*(?:arrow_drop_down|keyboard_arrow_down|expand_more))?'
                    for m in ('lite', 'fast', 'quality')}}


def validate_settings(value):
    if not isinstance(value, dict) or set(value) != set(ALLOWED):
        raise HTTPException(400, 'Cần đủ loại Video, chế độ, tỉ lệ, model và số kết quả; chưa hỗ trợ thời lượng.')
    for key, values in ALLOWED.items():
        if value[key] not in values or key == 'outputs' and type(value[key]) is not int:
            raise HTTPException(400, 'Cấu hình Flow không hợp lệ: ' + key)
    return dict(value)


CONTROLS = 'button,[role="button"],[role="tab"],[role="radio"],[role="option"],[role="menuitemradio"],[role="menuitem"],[role="combobox"]'
# Material icon text participates in accessible names on some Flow builds.
# Remove decorative nodes, rather than maintaining a list of icon spellings.
LABEL_JS = r'''e => {
    const c=e.cloneNode(true);
    c.querySelectorAll('i,svg,[aria-hidden="true"],[hidden],[class*="material-icons"],[class*="material-symbols"]').forEach(x=>x.remove());
    const norm=s=>String(s||'').replace(/\s+/g,' ').trim();
    return [...new Set([e.getAttribute('aria-label'),e.getAttribute('title'),c.textContent].map(norm).filter(Boolean))];
}'''


async def control(scope, pattern):
    marker = 'data-sf-setting-' + hashlib.sha256(pattern.pattern.encode()).hexdigest()[:12]
    await scope.locator(CONTROLS).evaluate_all('''(xs,{pattern,marker})=>{
        const labels=(''' + LABEL_JS + '''),re=new RegExp(pattern,'i');
        for(const e of xs){e.removeAttribute(marker);if(e.getClientRects().length && labels(e).some(s=>re.test(s)))e.setAttribute(marker,'');}
    }''', {'pattern': pattern.pattern, 'marker': marker})
    return scope.locator('['+marker+']').filter(visible=True)


def exact(pattern):
    return re.compile(r'^\s*(?:' + pattern + r')\s*$', re.I)


async def selected(item):
    return await item.evaluate('''e => {
        const states=['aria-selected','aria-pressed','aria-checked'].map(k=>e.getAttribute(k));
        if(states.includes('false')) return false;
        if(states.includes('true') || ['active','checked','on'].includes(e.getAttribute('data-state'))
            || e.matches('input:checked,option:checked'))return true;
        if(['inactive','unchecked','off'].includes(e.getAttribute('data-state')))return false;
        return null;
    }''')


async def settings_panel(page):
    # The real trigger's accessible name differs from its displayed summary.
    trigger = await control(page, exact('Settings trigger'))
    if await trigger.count() != 1:
        raise SettingsUnavailable('Chưa nhận diện duy nhất nút Settings trigger trên Flow.')
    anchor = await control(page, exact(LABELS['outputs'][1]))
    # Some Flow triggers omit aria-expanded. Do not toggle an already open panel.
    if await anchor.count() == 0:
        await trigger.click(timeout=5000)
    for _ in range(50):
        anchor = await control(page, exact(LABELS['outputs'][1]))
        if await anchor.count():break
        await asyncio.sleep(.1)
    if await anchor.count() != 1:
        raise SettingsUnavailable('Có nhiều bảng cài đặt Flow; chưa tự chọn.')
    # Find the smallest container holding all four setting groups, including portals.
    for depth in range(1, 9):
        candidate = anchor.locator(f'xpath=ancestor::*[{depth}]')
        if not await candidate.count() or await candidate.evaluate("e=>['BODY','HTML'].includes(e.tagName)"):
            break
        if (await (await control(candidate, exact(LABELS['kind']['video']))).count() == 1
                and await (await control(candidate, exact(LABELS['ratio']['9:16']))).count() == 1):
            return candidate
    raise SettingsUnavailable('Chưa xác định được vùng cài đặt Flow đầy đủ.')


async def read_settings(panel):
    actual = {}
    for key in ('kind', 'mode', 'ratio', 'outputs'):
        values = []
        for value, pattern in LABELS[key].items():
            item = await control(panel, exact(pattern))
            if await item.count() == 1 and await selected(item):
                values.append(value)
        actual[key] = values[0] if len(values) == 1 else None
    # A closed model trigger displays the currently chosen model.
    models = []
    for value, pattern in LABELS['model'].items():
        item = await control(panel, exact(pattern))
        if await item.count() == 1:
            models.append(value)
    actual['model'] = models[0] if len(models) == 1 else None
    return actual


async def snapshot_controls(scope):
    return await scope.locator(CONTROLS).evaluate_all('''xs=>{
        const labels=(''' + LABEL_JS + ''');
        return xs.filter(e=>e.getClientRects().length).slice(0,100).map(e=>({
            labels:labels(e).map(x=>x.slice(0,160)),role:e.getAttribute('role'),
            aria_selected:e.getAttribute('aria-selected'),aria_pressed:e.getAttribute('aria-pressed'),
            aria_checked:e.getAttribute('aria-checked'),data_state:e.getAttribute('data-state'),
            disabled:!!e.disabled,has_popup:e.getAttribute('aria-haspopup')
        }));
    }''')


async def apply_settings(page, desired, check, report):
    """Apply every requested control and distinguish clicks from verified states."""
    desired = validate_settings(desired)
    report['steps'] = []
    report['field_results'] = {}
    panel = None

    def phase(name):
        report['phase'] = name
        report['steps'].append(name)

    try:
        phase('check_account')
        await check()
        phase('open_settings_trigger')
        panel = await settings_panel(page)
        report['controls_before'] = await snapshot_controls(panel)
        report['observed_before'] = await read_settings(panel)
        unverified = []
        for key in ('kind', 'mode', 'ratio', 'outputs'):
            phase('select_' + key)
            await check()
            panel = await settings_panel(page)
            item = await control(panel, exact(LABELS[key][desired[key]]))
            if await item.count() != 1 or not await item.is_enabled():
                raise SettingsUnavailable('Flow chưa có lựa chọn duy nhất khả dụng: ' + key)
            before = await selected(item)
            result = {'before': before, 'clicked': False, 'after': before}
            report['field_results'][key] = result
            if before is not True:
                await item.click(timeout=5000)
                result['clicked'] = True
            # Reacquire after React updates; do not rely on stale element indices.
            for _ in range(20):
                panel = await settings_panel(page)
                item = await control(panel, exact(LABELS[key][desired[key]]))
                result['after'] = await selected(item) if await item.count() == 1 else None
                if result['after'] is True:
                    break
                await asyncio.sleep(.1)
            if result['after'] is False:
                raise SettingsUnavailable('Flow vẫn báo chưa chọn mục yêu cầu: ' + key)
            if result['after'] is None:
                unverified.append(key)
        phase('select_model')
        await check()
        panel = await settings_panel(page)
        model = panel.locator('button[aria-haspopup="listbox"],button[aria-haspopup="menu"],[role="combobox"]').filter(visible=True)
        if await model.count() != 1:
            model = await control(panel, re.compile(r'^(?:Veo\s*\d|Omni\s)', re.I))
        if await model.count() != 1:
            raise SettingsUnavailable('Chưa nhận diện duy nhất menu model của Flow.')
        current = await model.evaluate(LABEL_JS)
        if not any(re.fullmatch(LABELS['model'][desired['model']], name, re.I) for name in current):
            await model.click(timeout=5000)
            phase('choose_model_option')
            option = await control(page, exact(LABELS['model'][desired['model']]))
            for _ in range(30):
                option = await control(page, exact(LABELS['model'][desired['model']]))
                if await option.count() == 1:
                    break
                await asyncio.sleep(.1)
            if await option.count() != 1 or not await option.is_enabled():
                report['model_controls'] = await snapshot_controls(page)
                raise SettingsUnavailable('Model yêu cầu không có hoặc không khả dụng; không tự đổi sang model khác.')
            await check()
            await option.click(timeout=5000)
        phase('read_back_settings')
        for _ in range(20):
            await check()
            panel = await settings_panel(page)
            report['observed'] = await read_settings(panel)
            if report['observed'] == desired:
                return True
            await asyncio.sleep(.1)
        if report['observed'].get('model') != desired['model']:
            raise SettingsUnavailable('Model đọc lại trên Flow chưa khớp yêu cầu.')
        if unverified:
            report['unverified_fields'] = unverified
            return False
        raise SettingsUnavailable('Cấu hình đọc lại từ Flow chưa khớp yêu cầu. Không tạo video.')
    finally:
        if panel is not None:
            try:
                report['observed'] = await read_settings(panel)
                report['controls_after'] = await snapshot_controls(panel)
            except Exception:
                pass
        else:
            # Local diagnostic only: visible control labels and state attributes,
            # never cookies, HTML, storage, tokens or arbitrary page scripts.
            try:
                report['visible_controls'] = await snapshot_controls(page)
            except Exception:
                pass


def register_settings_routes(app, service):
    service.settings_report = None

    def status(rid):
        report = service.settings_report
        if not report or report['request_id'] != rid:
            raise HTTPException(404, 'Không có lượt đồng bộ cài đặt này trong phiên hiện tại.')
        return copy.deepcopy(report)

    async def run(report, aid, room, token):
        rid = report['request_id']
        async def check():
            current = service.account_bridge.selection()
            if (not current['available'] or current['account_id'] != aid
                    or current['token'] != token):
                raise SettingsUnavailable('Tài khoản đang chọn đã đổi; dừng đồng bộ cài đặt.')
            await service.assert_ready()
        try:
            # Reuse the uploaded project's open session to avoid interrupting upload.
            reuse = (service.connected and service.page and not service.page.is_closed()
                     and service.pinned_account == aid and service.pinned_room == room)
            service.pinned_account = aid
            service.pinned_room = room
            if not reuse:
                await service.disconnect_browser()
                await service.restore()
            verified = await apply_settings(service.page, report['requested'], check, report)
            if verified:
                report.update(state='verified', message='Đã đọc lại cấu hình khớp trên Flow. Chưa tạo video.')
            else:
                report.update(state='unverified', message='Đã bấm các lựa chọn yêu cầu nhưng chưa đọc được trạng thái xác nhận: '+', '.join(report.get('unverified_fields',[]))+'. Xem ảnh và tải báo cáo cài đặt; chưa tạo video.')
        except asyncio.CancelledError:
            report.update(state='failed', message='Đã dừng đồng bộ. Cài đặt trên Flow có thể đã đổi một phần; chưa tạo video.')
            raise
        except Exception as error:
            report['failed_phase'] = report.get('phase', 'open_project')
            report['error'] = {'type': type(error).__name__, 'detail': str(error)[:1800]}
            report.update(state='failed', message=(str(error) if isinstance(error, SettingsUnavailable)
                          else 'Chưa đồng bộ được cài đặt Flow ở bước '+report['failed_phase']+': ' + type(error).__name__)
                          + ' Có thể đã đổi một phần; chưa tạo video.')
        finally:
            try:
                if service.page and not service.page.is_closed():
                    try:
                        await service.page.screenshot(path=str(service.root / (rid + '.settings.png')), timeout=5000)
                        report['has_preview'] = True
                    except Exception:
                        pass
                    # Leave the upload toolbar accessible after taking evidence.
                    # Escape closes only the current popover; never click elsewhere.
                    try:
                        await service.page.keyboard.press('Escape')
                    except Exception:
                        pass
                (service.root / (rid + '.settings.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            finally:
                service.active = None

    @app.post('/local-api/flow/simple/settings')
    async def start(body: dict):
        desired = validate_settings(body.get('settings'))
        room = body.get('room_id')
        if not isinstance(room, str) or not room or len(room) > 100:
            raise HTTPException(400, 'Chưa xác định đúng phòng workflow.')
        async with service.gate:
            if service.busy():
                raise HTTPException(409, 'Flow đang có tác vụ; đợi hoàn tất trước khi đổi cài đặt.')
            if not service.account_bridge:
                raise HTTPException(409, 'Chọn tài khoản Flow tại tab Tài khoản.')
            selection = service.account_bridge.selection()
            if not selection['available'] or body.get('selection_token') != selection['token']:
                raise HTTPException(409, 'Tài khoản đã đổi hoặc chưa sẵn sàng; đọc lại lựa chọn.')
            if service.unresolved():
                raise HTTPException(409, 'Có lượt tạo chưa rõ kết quả; kiểm tra trước khi đổi cài đặt.')
            rid = 'flow-settings-' + secrets.token_hex(12)
            report = {'request_id': rid, 'state': 'running', 'requested': desired, 'observed': None,
                      'room_id': room, 'account_id': selection['account_id'], 'has_preview': False,
                      'message': 'Đang áp dụng cài đặt lên Flow; không gửi tạo video.'}
            service.settings_report = report
            service.active = rid
            service.task = asyncio.create_task(run(report, selection['account_id'], room, selection['token']))
            return status(rid)

    @app.get('/local-api/flow/simple/settings/{rid}')
    async def get_status(rid: str):
        return status(rid)

    @app.get('/local-api/flow/simple/settings/{rid}/preview')
    async def preview(rid: str):
        report = status(rid)
        if not report['has_preview']:
            raise HTTPException(404, 'Chưa có ảnh cài đặt Flow.')
        return FileResponse(service.root / (rid + '.settings.png'), media_type='image/png', headers={'Cache-Control': 'no-store'})
