"""Read-only readiness check for an app-owned Chrome/Edge debug endpoint.

Checks the browser-instance path in DevToolsActivePort, not just a live port.
No page access, navigation, authentication or credential export.
"""
from urllib.parse import urlsplit
import re
import httpx
from .google_login import flow_profile_path

async def probe_flow_browser(data,profile_key=None):
    failed=lambda code:{'ready':False,'code':code}
    try:
        rows=(flow_profile_path(data,profile_key)/'DevToolsActivePort').read_text().splitlines()
        port=int(rows[0]);browser_path=rows[1]
        if not 1<=port<=65535 or not re.fullmatch(r'/devtools/browser/[a-zA-Z0-9-]+',browser_path):raise ValueError()
    except (OSError,ValueError,IndexError):return failed('FLOW_BROWSER_PORT_NOT_READY')
    try:
        async with httpx.AsyncClient(trust_env=False,follow_redirects=False,timeout=2)as client:
            response=await client.get('http://127.0.0.1:'+str(port)+'/json/version')
        if response.status_code!=200:return failed('FLOW_BROWSER_ENDPOINT_UNAVAILABLE')
        if len(response.content)>1024*1024:return failed('FLOW_BROWSER_ENDPOINT_INVALID')
        body=response.json();url=urlsplit(body.get('webSocketDebuggerUrl',''))
        if url.scheme!='ws'or url.hostname not in ('127.0.0.1','localhost')or url.port!=port or url.path!=browser_path or url.username or url.password or url.query or url.fragment:
            return failed('FLOW_BROWSER_INSTANCE_MISMATCH')
        if not re.match(r'^(Chrome|Chromium|HeadlessChrome|Edg)/[0-9.]+$',str(body.get('Browser',''))):return failed('FLOW_BROWSER_ENDPOINT_INVALID')
        return {'ready':True,'endpoint':'http://127.0.0.1:'+str(port),'code':'FLOW_BROWSER_READY'}
    except Exception:return failed('FLOW_BROWSER_ENDPOINT_UNAVAILABLE')
