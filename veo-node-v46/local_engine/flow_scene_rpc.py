"""Direct reference-video adapter draft, with session ownership injected.

The application must supply its authenticated native-session RPC port. This is
not wired to live Flow: no challenge solver, cookie export, browser fingerprint
changes, or HTTP retry are provided here.
"""
from typing import Protocol
from uuid import uuid4

from .flow_scene_job import FlowAdapter, Identity, Prepared, Scene
from .flow_task_protocol import (
    REFERENCE_RPC, STATUS_RPC, DETAIL_RPC, UUID,
    UnsupportedFlowPayload, rpc_payload, submitted_media, media_status,
    asset_video_url,
)


def reference_payload(prompt, prepared, context, *, new_id=lambda: str(uuid4()).upper()):
    """One image, one output; schema observed in supplied Phoma Lc/jo/FE.

    context is ephemeral provider-owned request context for this project. The
    caller must obtain it through the normal Flow session; never serialize it
    into the job store or logs. Model determines eight-second Lite output in
    the inspected source. Portrait is enum 1, confirmed against callsite below.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError('prompt_required')
    if (not UUID.fullmatch(prepared.project_id) or
        not UUID.fullmatch(prepared.reference_media_id)):
        raise ValueError('prepared_identity_invalid')
    if not isinstance(context, list) or len(context) != 11 or context[5] != prepared.project_id:
        raise ValueError('native_request_context_required')
    return [[[
        [None, None, [[[prompt]]]],
        [[None, prepared.reference_media_id]],
        'veo_3_1_r2v_lite', 1, None,
        [None, None, None, None, new_id(), new_id()],
    ]], context, [new_id(), 2]]


class NativeSession(Protocol):
    async def check(self, account_id, project_id): ...
    async def prepare(self, scene: Scene) -> Prepared: ...
    async def reference_context(self, project_id): ...
    async def rpc(self, method, project_id, payload) -> tuple[int, bytes]: ...
    async def receive(self, identity: Identity, signed_url: str, request_id: str): ...


class DirectReferenceAdapter(FlowAdapter):
    def __init__(self, session: NativeSession):
        self.session = session

    async def check(self, account_id, project_id):
        await self.session.check(account_id, project_id)

    async def prepare(self, scene):
        return await self.session.prepare(scene)

    async def _rpc(self, method, project_id, payload):
        status, raw = await self.session.rpc(method, project_id, payload)
        if type(status) is not int or not 200 <= status < 300:
            # Non-2xx does not prove no work was accepted. Do not retry.
            raise UnsupportedFlowPayload('rpc_http_unconfirmed')
        return rpc_payload(raw, method)

    async def submit(self, scene, prepared):
        context = await self.session.reference_context(prepared.project_id)
        payload = reference_payload(scene.prompt, prepared, context)
        value = await self._rpc(REFERENCE_RPC, prepared.project_id, payload)
        identity = Identity(**submitted_media(value, prepared.project_id)).validate()
        if identity.media_id == prepared.reference_media_id:
            raise UnsupportedFlowPayload('submit_returned_reference_image')
        return identity

    async def status(self, identity):
        from dataclasses import asdict
        payload = await self._rpc(STATUS_RPC, identity.project_id,
                                  [None, None, [[identity.media_id]]])
        return media_status(payload, asdict(identity))['state']

    async def receive(self, identity, request_id):
        from dataclasses import asdict
        payload = await self._rpc(DETAIL_RPC, identity.project_id, [identity.media_id])
        url = asset_video_url(payload, asdict(identity))
        # The session adapter streams, ffprobes and atomically saves the file.
        # Signed URL is in memory only and is never returned to the workflow.
        return await self.session.receive(identity, url, request_id)
