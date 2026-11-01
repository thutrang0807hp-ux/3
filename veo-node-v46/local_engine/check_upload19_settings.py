"""Exercise the unchanged .19 toolbar upload followed by settings in one page."""
import asyncio
import hashlib
import importlib.util
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock
from PIL import Image
from playwright.async_api import async_playwright
from check_flow_settings import FIXTURE, module as settings

spec = importlib.util.spec_from_file_location('upload19', Path(__file__).with_name('simple_flow_upload.py'))
upload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload)

async def main():
    assert hashlib.sha256(Path(upload.__file__).read_bytes()).hexdigest() == '342e1bde247a0ca3612efe7c363cb0d741c84a1b014a71c35a402d1e6aba5869'
    with tempfile.TemporaryDirectory() as tmp:
        reference = Path(tmp)/'image.png'
        Image.new('RGB', (90,160), 'green').save(reference)
        fixture = FIXTURE.replace('<input type=file>', '') + '''
        <button aria-label="Add media menu" onclick="document.querySelector('#upload-menu').hidden=false">add</button>
        <div id=upload-menu hidden><button role=menuitem onclick="setTimeout(()=>{const e=document.createElement('input');e.type='file';e.accept='image/png';e.hidden=true;document.body.append(e);e.click()},300)">file_upload Upload</button></div>
        <button aria-label="Add ingredients to the prompt box" onclick="window.wrongComposer=true">add</button>
        '''
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            page = await browser.new_page()
            await page.set_content(fixture)
            report = {};logs=[]
            delivered = await upload.upload_to_project(page, reference, logs.append, report)
            assert delivered, report
            assert report['upload_implementation'] == 'project_upload_v46_19'
            assert 'click_upload_menu_item' in report['steps'] and report['phase'] == 'file_delivered', report
            actual = await page.locator('input[type=file]').evaluate('async e=>Array.from(new Uint8Array(await e.files[0].arrayBuffer()))')
            assert bytes(actual) == reference.read_bytes()
            await page.locator('#upload-menu').evaluate('e=>e.hidden=true')
            settings_report = {}
            assert await settings.apply_settings(page, settings.DEFAULTS, AsyncMock(), settings_report) is True
            assert settings_report['observed'] == settings.DEFAULTS
            assert not await page.evaluate('!!window.wrongComposer||!!window.sent')
            assert await page.locator('textarea').input_value() == 'Prompt untouched'
            await browser.close()
    print('PASS exact .19 uploader: Add media menu → Upload → delayed filechooser with exact image bytes; then settings readback in the same page; composer Add, prompt, Generate untouched.')

if __name__ == '__main__':
    asyncio.run(main())
