"""Shared, explicit selection and failover plans. No heuristic error rotation."""
import hashlib
import json
from fastapi import HTTPException


class AccountRejected(Exception):
    def __init__(self, reason):
        self.reason = reason


class AccountPool:
    def __init__(self, vault, service):
        self.vault, self.service = vault, service

    def rows(self):
        return sorted([a for a in self.vault.rows('accounts') if a.get('service') == self.service],
                      key=lambda a: (a.get('priority', 0), a['id']))

    @staticmethod
    def eligible(a):
        if a.get('service') == 'flow' and not a.get('engine_id') and not (a.get('login_transport')=='web_ui' and str(a.get('id','')).startswith('flow-web-')):
            return False
        return bool(a.get('enabled') and a.get('session_verified') and a.get('state') in ('ready', 'active'))

    def status(self):
        with self.vault.lock:
            rows = self.rows()
            selected = next((a for a in rows if a.get('active')), None)
            mode = (self.vault.secret(self.service + '-dispatch') or {}).get('mode')
            if mode not in ('selected', 'failover', 'balanced'):
                mode = 'balanced' if (self.vault.secret('rotation') or {}).get(self.service) else 'selected'
            ordered = ([selected] if selected else []) + [a for a in rows if a != selected]
            permitted = [a['id'] for a in ordered if self.eligible(a) and (mode != 'selected' or a == selected) and (a.get('login_transport')!='web_ui' or mode=='selected')]
            raw = [mode, selected['id'] if selected else None, self.vault.secret(self.service + '-video-slots'),
                   [[a['id'], bool(a.get('active')), bool(a.get('enabled')), a.get('state'), bool(a.get('session_verified'))] for a in rows]]
            return {'mode': mode, 'account_id': selected['id'] if selected else None,
                    'account_name': selected['name'] if selected else None, 'permitted': permitted,
                    'available': bool(permitted), 'token': hashlib.sha256(json.dumps(raw).encode()).hexdigest()}

    def select(self, body):
        mode, aid = body.get('mode'), body.get('account_id')
        if mode not in ('selected', 'failover', 'balanced'):
            raise HTTPException(400, 'Chọn dùng riêng, dự phòng theo thứ tự hoặc chia việc.')
        with self.vault.lock:
            rows = self.rows()
            if aid:
                chosen = next((a for a in rows if a['id'] == aid and self.eligible(a)), None)
                if not chosen and mode == 'selected':
                    raise HTTPException(409, 'Tài khoản chưa sẵn sàng.')
                if chosen:
                    for a in rows:
                        a['active'] = a['id'] == aid
                        self.vault.put('accounts', a)
            elif mode == 'selected' and not self.status()['account_id']:
                raise HTTPException(409, 'Chọn tài khoản trước.')
            if not any(self.eligible(a) for a in rows):
                raise HTTPException(409, 'Chưa có tài khoản sẵn sàng.')
            self.vault.set_secret(self.service + '-dispatch', {'mode': mode})
            rotation = self.vault.secret('rotation') or {}
            rotation[self.service] = mode != 'selected'
            self.vault.set_secret('rotation', rotation)
        return {'selection': self.status(), 'rotation': rotation,
                'message': 'Đã lưu lựa chọn dùng chung. Việc đã nhận giữ nguyên kế hoạch tài khoản.'}

    def limit(self, aid, reason):
        row = next((a for a in self.rows() if a['id'] == aid), None)
        if row:
            row.update(state='exhausted' if reason == 'quota' else 'expired', last_error=reason)
            self.vault.put('accounts', row)


def safe_rejection(result):
    """Only explicit structured rejections may authorize a new account attempt."""
    return (result.get('ok') is False and result.get('accepted') is False
            and result.get('reason') in ('quota', 'auth'))
