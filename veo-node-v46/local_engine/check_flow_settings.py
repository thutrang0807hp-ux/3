"""Browser fixture checks for the settings adapter, not certification of live Flow."""
import asyncio
import importlib.util
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright

spec = importlib.util.spec_from_file_location('flow_settings', Path(__file__).with_name('flow_settings.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

FIXTURE = '''<button aria-label="Settings trigger" aria-expanded=false onclick="this.setAttribute('aria-expanded','true');document.querySelector('#panel').hidden=false">Video · 720p · 8s</button>
<section id=panel hidden>
<div><button aria-pressed=true>Hình ảnh</button><button aria-pressed=false>Video</button></div>
<div><button aria-pressed=true>Khung hình</button><button aria-pressed=false>Thành phần</button></div>
<div><button aria-pressed=true>16:9</button><button aria-pressed=false>9:16</button></div>
<button id=model aria-haspopup=listbox onclick="document.querySelector('#models').hidden=false">Omni 1.1 Flash</button>
<div><button aria-pressed=false>x1</button><button aria-pressed=true>x2</button><button aria-pressed=false>x3</button><button aria-pressed=false>x4</button></div>
</section>
<div id=models role=listbox hidden><button role=option>Veo 3.1 - Fast</button><button role=option>Veo 3.1 - Lite</button><button role=option>Veo 3.1 - Quality</button></div>
<textarea>Prompt untouched</textarea><input type=file><button id=generate onclick="window.sent=true">Generate</button>
<script>
for(const button of document.querySelectorAll('[aria-pressed]'))button.onclick=()=>{for(const other of button.parentElement.children)other.setAttribute('aria-pressed','false');button.setAttribute('aria-pressed','true')};
for(const option of document.querySelectorAll('[role=option]'))option.onclick=()=>{document.querySelector('#model').textContent=option.textContent;document.querySelector('#models').hidden=true};
</script>'''

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        page = await browser.new_page()
        await page.set_content(FIXTURE)
        check = AsyncMock()
        report = {}
        await module.apply_settings(page, module.DEFAULTS, check, report)
        assert report['observed'] == module.DEFAULTS, report
        assert report['observed_before']['model'] is None
        assert await page.locator('textarea').input_value() == 'Prompt untouched'
        assert not await page.evaluate('!!window.sent')
        assert await page.locator('input').evaluate('e=>e.files.length') == 0
        # An already-open panel remains usable even without aria-expanded.
        await page.get_by_role('button', name='Settings trigger').evaluate("e=>e.removeAttribute('aria-expanded')")
        # Reapplying an identical request must not toggle any control.
        await page.evaluate("window.clicks=0;document.addEventListener('click',()=>window.clicks++)")
        await module.apply_settings(page, module.DEFAULTS, check, {})
        assert await page.evaluate('clicks') == 0
        # Change every supported field; x4 is output count, no duration interactions.
        desired = dict(module.DEFAULTS, mode='frames', ratio='16:9', model='fast', outputs=4)
        await module.apply_settings(page, desired, check, report)
        assert report['observed'] == desired
        # Material icon text is not the control label. Exercise a portal menu
        # and unrelated icon spellings, not a hand-maintained icon allowlist.
        decorated = FIXTURE.replace('>Video</button>', '><i class="material-symbols-outlined">movie</i>Video</button>').replace('>Thành phần</button>', '><i class="material-symbols-outlined">widgets</i>Thành phần</button>').replace('>9:16</button>', '><i class="material-symbols-outlined">crop_9_16</i>9:16</button>').replace('>Veo 3.1 - Lite</button>', '>Veo 3.1 - Lite<i class="material-symbols-outlined">check</i></button>')
        await page.set_content(decorated.replace("document.querySelector('#model').textContent=option.textContent", "document.querySelector('#model').innerHTML=option.innerHTML"))
        decorated_report = {}
        assert await module.apply_settings(page, module.DEFAULTS, check, decorated_report) is True
        assert decorated_report['observed'] == module.DEFAULTS
        assert decorated_report['controls_after']
        # Unknown state semantics must not prevent the remaining choices from
        # being attempted, and can never produce a verified result.
        await page.set_content(FIXTURE)
        await page.evaluate("for(const e of document.querySelectorAll('[aria-pressed]')){e.removeAttribute('aria-pressed');e.onclick=()=>{e.dataset.clicked='yes'}}")
        uncertain = {}
        assert await module.apply_settings(page, module.DEFAULTS, check, uncertain) is False
        assert set(uncertain['unverified_fields']) == {'kind','mode','ratio','outputs'}
        assert uncertain['observed']['model'] == 'lite'
        assert all(row['clicked'] for row in uncertain['field_results'].values())
        assert not await page.evaluate('!!window.sent')
        # Missing selected-state semantics cannot be treated as verified.
        await page.set_content(FIXTURE)
        await page.locator('button', has_text='Thành phần').evaluate("e=>e.onclick=()=>{}")
        try:
            await module.apply_settings(page, module.DEFAULTS, check, {})
            raise AssertionError('Unverified selection accepted')
        except module.SettingsUnavailable:
            pass
        assert not await page.evaluate('!!window.sent')
        # A missing Lite option must never silently substitute Fast.
        await page.set_content(FIXTURE)
        await page.get_by_role('option', name='Veo 3.1 - Lite', include_hidden=True).evaluate('e=>e.remove()')
        try:
            await module.apply_settings(page, module.DEFAULTS, check, {})
            raise AssertionError('Unavailable model accepted')
        except Exception as error:
            assert type(error).__name__ in ('TimeoutError', 'SettingsUnavailable'), error
        assert await page.locator('#model').inner_text() == 'Omni 1.1 Flash'
        # API lifecycle and account/busy guards with a real browser page.
        await page.set_content(FIXTURE)
        with tempfile.TemporaryDirectory() as tmp:
            current = {'available': True, 'account_id': 'fixture-account', 'token': 'fixture-token'}
            service = SimpleNamespace(root=Path(tmp), gate=asyncio.Lock(), task=None,
                active=None, connected=True, page=page, pinned_account='fixture-account', pinned_room='room',
                account_bridge=SimpleNamespace(selection=lambda: dict(current)),
                assert_ready=AsyncMock(), disconnect_browser=AsyncMock(), restore=AsyncMock(), unresolved=lambda: [])
            service.busy = lambda: service.task is not None and not service.task.done()
            app = FastAPI()
            module.register_settings_routes(app, service)
            endpoints = {r.path: r.endpoint for r in app.routes if hasattr(r,'endpoint')}
            start = endpoints['/local-api/flow/simple/settings']
            status = endpoints['/local-api/flow/simple/settings/{rid}']
            body = {'settings': module.DEFAULTS, 'room_id': 'room', 'selection_token': 'fixture-token'}
            try:
                await start(dict(body, selection_token='stale'))
                raise AssertionError('Stale account selection accepted')
            except HTTPException as error:
                assert error.status_code == 409
            receipt = await start(body)
            try:
                await start(body)
                raise AssertionError('Concurrent operation accepted')
            except HTTPException as error:
                assert error.status_code == 409
            await service.task
            result = await status(receipt['request_id'])
            assert result['state'] == 'verified' and result['has_preview'], result
            assert service.active is None and service.restore.await_count == 0
            assert (Path(tmp)/(receipt['request_id']+'.settings.json')).is_file()
            # Change selected account while a settings request is starting.
            await page.set_content(FIXTURE)
            receipt = await start(body)
            current['account_id'] = 'other-account'
            await service.task
            result = await status(receipt['request_id'])
            assert result['state'] == 'failed' and 'Tài khoản' in result['message'], result
            assert not await page.evaluate('!!window.sent')
        await browser.close()
    print('PASS settings browser fixtures: state readback, idempotency, all fields, unknown current model, unsupported model, missing state, API lifecycle, busy/account guards; no prompt/upload/generation.')

if __name__ == '__main__':
    asyncio.run(main())
