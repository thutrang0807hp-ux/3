"""Sanitized account inventory from the owned Flow engine extension."""
import json
import hashlib
import time
from fastapi import HTTPException
from .account_pool import AccountPool
from .flow_connection import error as flow_error, validate as validate_flow, MESSAGES, safe_details


class FlowAccounts:
    def __init__(self, flow):
        self.flow, self.vault = flow, flow.vault
        self.pool = AccountPool(self.vault, 'flow')
        self.locks = {}

    async def request(self, method, path, body=None):
        config = self.flow.config()
        if not config.get('key'):
            raise flow_error('FLOW_ENGINE_NOT_CONFIGURED','engine')
        try:
            async with self.flow.client_factory() as client:
                response = await client.request(method, config['url'] + '/sceneforge/' + path,
                    headers={'Authorization': 'Bearer ' + config['key']}, json=body, timeout=120)
                if len(response.content) > 1024**2:raise flow_error('FLOW_ENGINE_REJECTED','engine')
                if response.status_code != 200:
                    try:detail=response.json().get('detail')
                    except Exception:detail=None
                    if isinstance(detail,dict) and detail.get('code')in MESSAGES:
                        safe=safe_details(detail);stage=safe.pop('stage','engine')
                        raise flow_error(detail['code'],stage,**safe)
                    raise flow_error('FLOW_ENGINE_REJECTED','engine')
                return response.json()
        except HTTPException:raise
        except Exception:
            raise flow_error('FLOW_ENGINE_UNREACHABLE','engine') from None

    async def sync(self):
        data = await self.request('GET', 'accounts')
        if data.get('protocol') != 'sceneforge-account-pin-v1' or data.get('single_attempt') is not True:
            raise HTTPException(409, 'Cần engine có ghim tài khoản và một lần gửi.')
        rows = data.get('accounts', [])
        if not isinstance(rows, list) or len(rows) > 200:
            raise HTTPException(502, 'Danh sách engine chưa hợp lệ.')
        ids = set()
        config = self.flow.config()
        identity = hashlib.sha256((config['url'] + config['key']).encode()).hexdigest()
        for r in rows:
            if type(r.get('id')) is not int or r['id'] < 1:
                raise HTTPException(502, 'Mã tài khoản engine chưa hợp lệ.')
            aid = 'flow-engine-' + str(r['id'])
            ids.add(aid)
            previous = next((a for a in self.pool.rows() if a['id'] == aid), {})
            if previous.get('engine_instance') != identity:
                previous = {}
            self.vault.put('accounts', {**previous, 'id': aid, 'service': 'flow', 'name': str(r.get('name', aid))[:80],
                'engine_id': r['id'], 'engine_instance': identity, 'native_route_id':r.get('native_route_id'), 'enabled': bool(r.get('enabled')) and previous.get('enabled', True),
                'state': previous.get('state', 'unverified'), 'session_verified': previous.get('session_verified', False),
                'active': previous.get('active', False), 'priority': previous.get('priority', len(ids)),
                'credit': previous.get('credit'), 'engine_seen': time.time()})
        for row in self.pool.rows():
            if row.get('engine_id') and row['id'] not in ids:
                row.update(session_verified=False, state='unverified')
                self.vault.put('accounts', row)
        config = self.flow.config()
        config['account_binding'] = True
        config['task_journal'] = data.get('task_journal')is True
        self.vault.set_secret('flow-engine', config)
        return {'accounts': self.pool.rows(), 'selection': self.pool.status()}

    async def check(self, aid):
        row = next((a for a in self.pool.rows() if a['id'] == aid), None)
        if row and row.get('login_transport')=='web_ui'and getattr(self,'web_ui',None):
            try:
                await self.web_ui.verify(aid)
                row.update(session_verified=True,state='ready');self.vault.put('accounts',row)
                return {'ok':True,'checked':True,'credit':None}
            except Exception:
                row.update(session_verified=False,state='unverified');self.vault.put('accounts',row)
                return {'ok':False,'accepted':None,'reason':'unknown'}
        if not row or not row.get('engine_id'):
            raise HTTPException(409, 'Đồng bộ tài khoản từ engine Flow trước.')
        result = await self.request('POST', 'accounts/' + str(row['engine_id']) + '/check', {})
        if result.get('ok'):
            row.update(session_verified=True, state='ready', credit=result.get('credit'), credit_at=time.time())
            self.vault.put('accounts', row)
            if not any(a.get('active') for a in self.pool.rows()):
                self.pool.select({'mode': 'selected', 'account_id': aid})
        else:
            row.update(session_verified=False,state='unverified');self.vault.put('accounts',row)
        return result

    async def prepare_concurrency(self, aid, kind='video'):
        row = next(a for a in self.pool.rows() if a['id'] == aid)
        expected = self.flow.image_slots.limit() if kind=='image' else self.flow.video_slots.limit()
        path = '/image-concurrency' if kind=='image' else '/concurrency'
        result = await self.request('POST', 'accounts/' + str(row['engine_id']) + path, {'per_account': expected})
        if result.get('per_account') != expected or kind=='image' and result.get('kind')!='image':
            raise HTTPException(409, 'Engine chưa xác nhận mức đồng thời đúng loại ảnh/clip; cập nhật và khởi động lại engine, chưa gửi tạo.')

    async def import_session(self, cookies, browser_context=None, browser_route=None):
        validate_flow(cookies)
        imported = await self.request('POST', 'accounts', {'cookies': cookies, **({'browser_context':browser_context} if browser_context else {}), **({'browser_route':browser_route} if browser_route else {})})
        result = await self.sync()
        if type(imported.get('id')) is int and imported['id'] > 0:
            result['imported_account_id'] = 'flow-engine-' + str(imported['id'])
        return result

    async def remove(self, aid):
        if aid in self.flow.assignments.values():
            raise HTTPException(409, 'Đợi các việc Flow của tài khoản hoàn tất.')
        row = next((a for a in self.pool.rows() if a['id'] == aid), None)
        if row and row.get('login_transport')=='web_ui':
            release=getattr(getattr(self,'web_ui',None),'release_account',None)
            if release:await release(aid)
            binding=(self.vault.secret('flow-extension-ui')or{})
            if binding.get('account_id')==aid:
                if getattr(self,'native_relay',None):self.native_relay.revoke(binding['route_id'])
                self.vault.delete_secret('flow-extension-ui')
            profiles=self.vault.secret('flow-managed-profiles')or{}
            if aid in profiles:
                profiles.pop(aid);self.vault.set_secret('flow-managed-profiles',profiles)
            self.vault.delete('accounts',aid)
            if (self.vault.secret('flow-ui-profile')or{}).get('account_id')==aid:self.vault.delete_secret('flow-ui-profile')
            return
        if row and row.get('engine_id'):
            await self.request('DELETE', 'accounts/' + str(row['engine_id']))
            if row.get('native_route_id') and getattr(self,'native_relay',None):self.native_relay.revoke(row['native_route_id'])


def install_flow_accounts(app, flow):
    service = FlowAccounts(flow)
    flow.account_service = service
    @app.post('/local-api/flow/accounts/sync')
    async def sync(body: dict):
        return await service.sync()
    @app.post('/local-api/flow/accounts/import')
    async def import_session(body: dict):
        return await service.import_session(body.get('cookies'),body.get('browser_context'))
    @app.post('/local-api/flow/concurrency')
    async def concurrency(body: dict):
        return flow.video_slots.configure(body, bool(flow.tasks))
    @app.post('/local-api/flow/image-concurrency')
    async def image_concurrency(body: dict):
        return flow.image_slots.configure(body, bool(flow.tasks))
    @app.post('/local-api/flow/selection')
    async def select(body: dict):
        return service.pool.select(body)
    return service
