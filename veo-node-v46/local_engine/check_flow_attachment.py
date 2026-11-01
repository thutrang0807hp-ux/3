"""Composer chips can be small/cropped or above the inner prompt form."""
import asyncio,base64,io,tempfile
from pathlib import Path
from unittest.mock import AsyncMock
from PIL import Image,ImageOps
from playwright.async_api import async_playwright
from .check_flow_prepare import SETTINGS
from .flow_prepare import attached_reference,prepare_composer
from .flow_settings import DEFAULTS

async def main():
 with tempfile.TemporaryDirectory()as tmp:
  source=Image.new('RGB',(90,160));source.putdata([((x*3)%256,(y*2)%256,(x+y)%256)for y in range(160)for x in range(90)]);p=Path(tmp)/'source.png';source.save(p)
  chip=io.BytesIO();ImageOps.fit(source,(24,24)).save(chip,format='PNG');url='data:image/png;base64,'+base64.b64encode(chip.getvalue()).decode()
  other=io.BytesIO();Image.new('RGB',(24,24),'blue').save(other,format='PNG');wrong='data:image/png;base64,'+base64.b64encode(other.getvalue()).decode()
  async with async_playwright()as pw:
   browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page()
   # A library card outside the composer must never prove an attachment.
   library='<article><img width=90 height=160 src="'+url+'"><button aria-label="More options">more_vert</button></article>'
   outer='<div id=outer style="width:500px"><div id=attachments><img width=48 height=48 src="'+url+'"></div><form onsubmit="return false"><textarea></textarea><button type=button onclick="window.sent=true">Generate</button></form></div>'
   await page.set_content(SETTINGS+library+outer+"<script>document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelector('#settings').hidden=true})</script>")
   await page.wait_for_function('Array.from(document.images).every(i=>i.complete)')
   report={};assert await attached_reference(page,source,report=report),report
   assert report['attachment_probe']['images'][0]['natural_width']==24
   assert report['attachment_probe']['verified_by']=='small_thumbnail_pixels'
   await prepare_composer(page,p,'Wave once.',DEFAULTS,AsyncMock(),report)
   assert await page.locator('textarea').input_value()=='Wave once.' and not await page.evaluate('!!window.sent')
   await page.locator('#attachments img').evaluate('(e,url)=>e.src=url',wrong);await page.wait_for_function('Array.from(document.images).every(i=>i.complete)')
   assert not await attached_reference(page,source)
   await page.locator('#attachments').evaluate('e=>e.innerHTML=""')
   assert not await attached_reference(page,source) # Library image alone is insufficient.
   # A CSS-backed chip can be attributed by its already-matched media ID.
   await page.locator('#attachments').evaluate('(e,url)=>e.innerHTML=`<div data-media-id="chosen-media" style="width:48px;height:48px;background-image:url(${url})"></div>`',url)
   report={};assert await attached_reference(page,source,'chosen-media',report),report
   assert report['attachment_probe']['verified_by']=='media_id'
   assert not await attached_reference(page,source,'other-media')
   # On restart a CSS chip has no remembered binding; only a matching library
   # media ID may establish its relationship to the original scene image.
   original=io.BytesIO();source.save(original,format='PNG');full='data:image/png;base64,'+base64.b64encode(original.getvalue()).decode()
   await page.locator('article').evaluate("e=>e.dataset.mediaId='chosen-media'")
   await page.locator('article img').evaluate('(e,url)=>e.src=url',full)
   await page.wait_for_function('Array.from(document.images).every(i=>i.complete)')
   report={};assert await attached_reference(page,source,report=report),report
   assert report['attachment_probe']['verified_by']=='media_id_from_matched_library'
   await page.locator('#attachments').evaluate("e=>e.innerHTML=''")
   assert not await attached_reference(page,source)

   # Some editors keep the image inline; typing must not clear that image.
   inline=SETTINGS+'<form onsubmit="return false"><div contenteditable=true role=textbox><img width=48 height=48 src="'+url+'"></div><button type=button onclick="window.sent=true">Generate</button></form>'+"<script>document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelector('#settings').hidden=true})</script>"
   await page.set_content(inline);await page.wait_for_function('Array.from(document.images).every(i=>i.complete)')
   report={};await prepare_composer(page,p,'Wave once.',DEFAULTS,AsyncMock(),report)
   assert await page.locator('[contenteditable] img').count()==1
   assert 'Wave once.' in await page.locator('[contenteditable]').inner_text()
   assert not await page.evaluate('!!window.sent')
   await browser.close()
 print('PASS attachment: 24px cropped chip above inner form verified; exact prompt filled without Generate; wrong chip and library-only rejected; CSS chip requires matching media ID.')

if __name__=='__main__':asyncio.run(main())
