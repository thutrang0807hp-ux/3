"""Review draft: durable one-scene workflow, independent of SimpleFlow/UI.

The adapter owns the existing account/profile and native Flow session. This
module never extracts credentials or retries a generation. A transport failure
after dispatch is ambiguous, including cancellation and process termination.
"""
import asyncio
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from .flow_task_protocol import FlowRpcRejected, UUID


@dataclass(frozen=True)
class Scene:
    request_id: str
    account_id: str
    room_id: str
    scene_id: str
    part: str
    prompt: str
    image: Path

    def fingerprint(self):
        if not all(isinstance(v, str) and v.strip() for v in
                   (self.request_id, self.account_id, self.room_id,
                    self.scene_id, self.part, self.prompt)):
            raise ValueError('scene_fields_required')
        digest = hashlib.sha256(self.image.read_bytes()).hexdigest()
        fields = [self.account_id, self.room_id, self.scene_id, self.part,
                  self.prompt, digest, 'ingredients/lite/9:16/8s/x1']
        return hashlib.sha256(json.dumps(fields, ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class Identity:
    media_id: str
    project_id: str
    workflow_id: str

    def validate(self):
        if not all(isinstance(v, str) and UUID.fullmatch(v)
                   for v in asdict(self).values()):
            raise ValueError('provider_identity_invalid')
        return self


@dataclass(frozen=True)
class Prepared:
    account_id: str
    project_id: str
    reference_media_id: str


class FlowAdapter(Protocol):
    """No raw RPC response, credential or signed URL enters the durable store.

    prepare must resolve/upload the selected image into the room's project.
    submit must make exactly one native-session request, with no inner retry.
    receive must stream and validate the video before atomically promoting it
    into app storage; it returns a local path, never a remote URL.
    """
    async def check(self, account_id: str, project_id: str | None): ...
    async def prepare(self, scene: Scene) -> Prepared: ...
    async def submit(self, scene: Scene, prepared: Prepared) -> Identity: ...
    async def status(self, identity: Identity) -> str: ...
    async def receive(self, identity: Identity, request_id: str) -> Path: ...


class SceneStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS scene_jobs (
                request_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
                account_id TEXT NOT NULL, room_id TEXT NOT NULL,
                scene_id TEXT NOT NULL, part TEXT NOT NULL,
                state TEXT NOT NULL, identity TEXT, result TEXT, error TEXT)''')
            # One unresolved job per account protects the shared browser session.
            db.execute('''CREATE UNIQUE INDEX IF NOT EXISTS one_flow_scene_per_account
                ON scene_jobs(account_id) WHERE state NOT IN
                ('done', 'prepare_failed', 'rejected', 'failed')''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
        finally:
            db.close()

    def get(self, request_id):
        with self.connect() as db:
            row = db.execute('SELECT * FROM scene_jobs WHERE request_id=?',
                             (request_id,)).fetchone()
        if row is None:
            raise KeyError(request_id)
        record = dict(row)
        for field in ('identity', 'result', 'error'):
            record[field] = json.loads(record[field]) if record[field] else None
        return record

    def reserve(self, scene):
        fingerprint = scene.fingerprint()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT fingerprint FROM scene_jobs WHERE request_id=?',
                             (scene.request_id,)).fetchone()
            if row:
                if row['fingerprint'] != fingerprint:
                    raise ValueError('request_id_content_changed')
                return False
            db.execute('''INSERT INTO scene_jobs
                (request_id,fingerprint,account_id,room_id,scene_id,part,state)
                VALUES (?,?,?,?,?,?,?)''',
                       (scene.request_id, fingerprint, scene.account_id,
                        scene.room_id, scene.scene_id, scene.part, 'preparing'))
        return True

    def transition(self, request_id, expected, state, *, identity=None,
                   result=None, error=None):
        with self.connect() as db:
            changed = db.execute('''UPDATE scene_jobs SET state=?,
                identity=COALESCE(?,identity), result=COALESCE(?,result), error=?
                WHERE request_id=? AND state=?''',
                (state, json.dumps(identity) if identity is not None else None,
                 json.dumps(result) if result is not None else None,
                 json.dumps(error) if error is not None else None,
                 request_id, expected)).rowcount
            if changed != 1:
                raise RuntimeError('job_state_changed')


class SceneWorkflow:
    def __init__(self, store: SceneStore, adapter: FlowAdapter, *,
                 sleep=asyncio.sleep, poll_interval=10, max_polls=30):
        if poll_interval < 0 or max_polls < 1:
            raise ValueError('invalid_poll_limits')
        self.store, self.adapter = store, adapter
        self.sleep, self.poll_interval, self.max_polls = sleep, poll_interval, max_polls
        self._lock = asyncio.Lock()

    async def create(self, scene: Scene):
        """Only a newly reserved request can dispatch. Repeated calls only read."""
        async with self._lock:
            if not self.store.reserve(scene):
                return self.store.get(scene.request_id)
            try:
                await self.adapter.check(scene.account_id, None)
                prepared = await self.adapter.prepare(scene)
                if (prepared.account_id != scene.account_id or
                    not all(isinstance(v, str) and UUID.fullmatch(v)
                            for v in (prepared.project_id, prepared.reference_media_id))):
                    raise ValueError('prepared_binding_invalid')
                await self.adapter.check(scene.account_id, prepared.project_id)
                # Recheck the source file after preparation, before dispatch.
                if scene.fingerprint() != self.store.get(scene.request_id)['fingerprint']:
                    raise ValueError('scene_changed_during_prepare')
            except BaseException:
                self.store.transition(scene.request_id, 'preparing', 'prepare_failed',
                                      error={'code': 'preparation_failed'})
                raise
            # Commit the ambiguity boundary BEFORE calling the provider.
            self.store.transition(scene.request_id, 'preparing', 'dispatching')
            try:
                identity = (await self.adapter.submit(scene, prepared)).validate()
                if (identity.project_id != prepared.project_id or
                    identity.media_id == prepared.reference_media_id):
                    raise ValueError('submit_identity_mismatch')
            except FlowRpcRejected as error:
                # Fixed numeric/public error codes only; never persist raw bodies.
                details = error.details
                safe = {'code': 'rpc_rejected'}
                value = details.get('rpc_error_code')
                if type(value) is int and 0 <= value <= 999:
                    safe['rpc_error_code'] = value
                import re
                safe['public_error_codes'] = [v for v in details.get('public_error_codes', [])
                    if isinstance(v, str) and re.fullmatch(r'PUBLIC_ERROR_[A-Z0-9_]{1,100}', v)][:8]
                self.store.transition(scene.request_id, 'dispatching', 'rejected', error=safe)
                return self.store.get(scene.request_id)
            except BaseException:
                self.store.transition(scene.request_id, 'dispatching', 'unknown',
                                      error={'code': 'submission_unconfirmed'})
                raise
            # If this commit fails, dispatching remains: never send again.
            self.store.transition(scene.request_id, 'dispatching', 'pending',
                                  identity=asdict(identity))
            return await self._follow(scene.request_id)

    async def follow(self, request_id):
        """Explicitly resume reads/download after restart; never calls submit."""
        async with self._lock:
            return await self._follow(request_id)

    async def _follow(self, request_id):
        record = self.store.get(request_id)
        if record['state'] not in ('pending', 'receiving'):
            return record
        identity = Identity(**record['identity']).validate()
        for _ in range(self.max_polls):
            await self.adapter.check(record['account_id'], identity.project_id)
            if record['state'] == 'pending':
                await self.sleep(self.poll_interval)
                await self.adapter.check(record['account_id'], identity.project_id)
                status = await self.adapter.status(identity)
                if status == 'failed':
                    self.store.transition(request_id, 'pending', 'failed',
                                          error={'code': 'provider_generation_failed'})
                    return self.store.get(request_id)
                if status == 'pending':
                    continue
                if status != 'success':
                    raise ValueError('unsupported_provider_status')
                self.store.transition(request_id, 'pending', 'receiving')
                record = self.store.get(request_id)
            # Adapter must use deterministic app storage by request_id, allowing
            # a crash after download but before the final commit to resume safely.
            path = await self.adapter.receive(identity, request_id)
            if not isinstance(path, Path) or not path.is_file() or path.stat().st_size == 0:
                raise ValueError('validated_local_video_required')
            result = {'file': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                      'room_id': record['room_id'], 'scene_id': record['scene_id'],
                      'part': record['part'], 'provider_identity': asdict(identity)}
            self.store.transition(request_id, 'receiving', 'done', result=result)
            return self.store.get(request_id)
        # A poll budget expiring is not a generation failure. Keep the ID for
        # explicit follow() later; a repeated create() cannot send another request.
        return self.store.get(request_id)
