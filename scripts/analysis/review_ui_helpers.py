"""Navigate the redesigned review tabs before exercising a legacy control."""
async def ensure_review_tab(page,selector):
 dialog=page.locator('#anCaptionDialog')
 if not await dialog.locator('[data-cap-panel]').count():return
 if 'logo'in selector.lower():tab='logo'
 elif any(key in selector for key in ['caption-style','data-cap-color','bg-color','bg-enabled','bg-opacity','data-cap-words','data-cap-size','data-cap-y','data-cap-review','data-cap-cue']):tab='captions'
 elif any(key in selector for key in ['data-cap-export-size','data-cap-diagnostics','data-cap-status']):tab='export'
 elif any(key in selector for key in ['data-cap-rate','data-cap-trim','data-cap-end','data-cap-cut-clip','data-cap-frame','data-cap-listen','data-cap-source','data-cap-reset','data-cap-final-rate','data-cap-joined','data-cap-transition']):tab='assemble'
 else:return
 button=dialog.locator('[data-cap-panel='+tab+']')
 if await button.get_attribute('aria-selected')!='true':await button.click()
 if any(key in selector for key in ['data-cap-rate','data-cap-trim']):
  details=dialog.locator('[data-cap-advanced]')
  if not await details.evaluate('el=>el.open'):await details.locator('summary').click()
 if tab=='logo'and 'summary'not in selector:
  details=dialog.locator('.anLogoTools')
  if not await details.evaluate('el=>el.open'):await details.locator('summary').click()
