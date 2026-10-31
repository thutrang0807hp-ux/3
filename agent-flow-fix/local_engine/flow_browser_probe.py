"""Read-only readiness check for an app-owned Chrome/Edge debug endpoint.

Checks the browser-instance path in DevToolsActivePort, not just a live port.
No page access, navigation, authentication or credential export.
"""
from urllib.parse import urlsplit
import re
import asyncio
import httpx
from .google_login import flow_profile_path

async def probe_flow_browser(data,profile_key=None):
    failed=lambda code:{'ready':False,'code':code}
    try:
        rows=(flow_profile_path(data,profile_key)/'DevToolsActivePort').read_text().splitlines()
        port=int(rows[0]);browser_path=rows[1]
        if not 1<=port<=65535 or not re.fullmatch(r'/devtools/browser/[a-zA-Z0-9-]+',browser_path):raise ValueError()
    except (OSError,ValueError,IndexError):
        port = 9333
        browser_path = None
        try:
            async with httpx.AsyncClient(trust_env=False,follow_redirects=False,timeout=2) as client:
                r = await client.get('http://127.0.0.1:9333/json/version')
            if r.status_code == 200:
                return {'ready':True,'endpoint':'http://127.0.0.1:9333','code':'FLOW_BROWSER_READY','detail':'fixed-port'}
        except Exception:
            pass
        return failed('FLOW_BROWSER_PORT_NOT_READY')
    last_err = 'none'
    response = None
    hosts = ['127.0.0.1', 'localhost']
    for attempt in range(6):
        host = hosts[attempt % len(hosts)]
        try:
            async with httpx.AsyncClient(trust_env=False,follow_redirects=False,timeout=3) as client:
                response = await client.get('http://'+host+':'+str(port)+'/json/version')
            if response.status_code == 200:
                break
            last_err = host+':status_'+str(response.status_code)
        except Exception as e:
            last_err = host+':'+type(e).__name__+':'+str(e)[:80]
            response = None
        if attempt < 5:
            await asyncio.sleep(0.6)
    if response is None or response.status_code != 200:
        return {'ready':False,'code':'FLOW_BROWSER_ENDPOINT_UNAVAILABLE','detail':'port='+str(port)+' err='+last_err}
    try:
        if len(response.content)>1024*1024:return failed('FLOW_BROWSER_ENDPOINT_INVALID')
        body=response.json();url=urlsplit(body.get('webSocketDebuggerUrl',''))
        if url.scheme!='ws' or url.hostname not in ('127.0.0.1','localhost') or url.port!=port or url.path!=browser_path or url.username or url.password or url.query or url.fragment:
            return failed('FLOW_BROWSER_INSTANCE_MISMATCH')
        if not re.match(r'^(Chrome|Chromium|HeadlessChrome|Edg)/[0-9.]+$',str(body.get('Browser',''))):return failed('FLOW_BROWSER_ENDPOINT_INVALID')
        return {'ready':True,'endpoint':'http://127.0.0.1:'+str(port),'code':'FLOW_BROWSER_READY'}
    except Exception as e:
        return {'ready':False,'code':'FLOW_BROWSER_ENDPOINT_UNAVAILABLE','detail':'parse:'+type(e).__name__}
