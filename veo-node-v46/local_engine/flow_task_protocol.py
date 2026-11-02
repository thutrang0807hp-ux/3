"""Strict, versioned Flow batch readers. No network I/O or generation calls.

The schema comes from static inspection of Phoma 1.6.2, not a live Flow capture.
Unsupported/ambiguous shapes never fall back to scanning for arbitrary UUIDs.
"""
import json
import re
from urllib.parse import parse_qsl, urlsplit
from .flow_network_protocol import LIMIT, decode_transport

BATCH_PATH = '/_/AiSandboxAngularFrontend/data/batchexecute'
REFERENCE_RPC = 'MZZa6b'
STATUS_RPC = 'jwpduf'
DETAIL_RPC = 'as29s'
SCHEMA = 'flow_reference_batch_v1_draft'
UUID = re.compile(r'^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$')
MEDIA = re.compile(UUID.pattern[:-1] + r'(?:_upsampled)?$')
ERROR_CODE = re.compile(r'^PUBLIC_ERROR_[A-Z0-9_]{1,100}$')


class UnsupportedFlowPayload(ValueError):
    """Only fixed codes may escape; never embed raw bodies or URLs in errors."""


class FlowRpcRejected(UnsupportedFlowPayload):
    def __init__(self, details):
        super().__init__('rpc_rejected')
        self.details=details


def _rpc_error_details(error, rows):
    """Keep only numeric status / exact PUBLIC_ERROR_* codes, never messages."""
    details={}
    if isinstance(error,list) and error and type(error[0])is int and 0<=error[0]<=999:
        details['rpc_error_code']=error[0]
    codes=set();budget=500
    def walk(value,depth=0):
        nonlocal budget
        budget-=1
        if budget<0 or depth>10:return
        if isinstance(value,str) and ERROR_CODE.fullmatch(value):codes.add(value)
        elif isinstance(value,list):
            for item in value[:80]:walk(item,depth+1)
    walk(error)
    if codes:details['public_error_codes']=sorted(codes)[:8]
    statuses={row[1] for row in rows if len(row)>1 and row[0] in ('di','af.httprm') and type(row[1])is int and 400<=row[1]<=599}
    if len(statuses)==1:details['rpc_http_status']=statuses.pop()
    return details


def normalize(text):
    return ' '.join(text.split())


def project_from_url(url):
    u = urlsplit(url)
    if (u.scheme != 'https' or u.hostname != 'flow.google.com' or
            u.port not in (None, 443) or u.username or u.password):
        raise UnsupportedFlowPayload('project_origin')
    match = re.fullmatch(r'/project/([a-zA-Z0-9_-]+)/?', u.path)
    if not match:
        raise UnsupportedFlowPayload('project_path')
    return match[1]


def batch_endpoint(url):
    u = urlsplit(url)
    return (u.scheme == 'https' and u.hostname == 'flow.google.com' and
            u.port in (None, 443) and not u.username and not u.password and u.path == BATCH_PATH)


def _at(value, *indices):
    for index in indices:
        if not isinstance(value, list) or len(value) <= index:
            raise UnsupportedFlowPayload('array_shape')
        value = value[index]
    return value


def _id(value, pattern=UUID):
    return isinstance(value, str) and bool(pattern.fullmatch(value))


def reference_request(raw, content_type, expected_prompt, project_id):
    """Exactly one Ingredients request, one output, exact text and project.

    Inline reference-tag prompt rewriting is unsupported until captured live.
    Only the prompt field is compared; tokens/metadata strings are never searched.
    """
    if content_type.split(';', 1)[0].strip().lower() != 'application/x-www-form-urlencoded':
        raise UnsupportedFlowPayload('request_media_type')
    if isinstance(raw, str):
        raw = raw.encode('utf-8')
    if not isinstance(raw, bytes) or len(raw) > LIMIT:
        raise UnsupportedFlowPayload('request_limit')
    fields = parse_qsl(raw.decode('utf-8'), max_num_fields=40, errors='strict')
    envelopes = [v for k, v in fields if k == 'f.req']
    if len(envelopes) != 1:
        raise UnsupportedFlowPayload('request_envelope_count')
    outer = json.loads(envelopes[0])
    if not isinstance(outer, list) or len(outer) != 1:
        raise UnsupportedFlowPayload('request_group_count')
    group = outer[0]
    if not isinstance(group, list) or len(group) != 1:
        raise UnsupportedFlowPayload('request_rpc_count')
    call = group[0]
    if not isinstance(call, list) or len(call) < 2 or call[0] != REFERENCE_RPC:
        raise UnsupportedFlowPayload('request_not_ingredients_video')
    if not isinstance(call[1], str):
        raise UnsupportedFlowPayload('request_payload_type')
    payload = json.loads(call[1])
    rows = _at(payload, 0)
    if not isinstance(rows, list) or len(rows) != 1:
        raise UnsupportedFlowPayload('request_output_count')
    if _at(payload, 1, 5) != project_id:
        raise UnsupportedFlowPayload('request_project_mismatch')
    parts = _at(rows, 0, 0, 2, 0)
    if not isinstance(parts, list) or not 1 <= len(parts) <= 80:
        raise UnsupportedFlowPayload('request_prompt_shape')
    # Text-only prompt parts: no substring matching against the whole payload.
    if any(not isinstance(p, list) or len(p) != 1 or not isinstance(p[0], str) for p in parts):
        raise UnsupportedFlowPayload('request_structured_reference_prompt_unsupported')
    if normalize(''.join(p[0] for p in parts)) != normalize(expected_prompt):
        raise UnsupportedFlowPayload('request_prompt_mismatch')
    references = _at(rows, 0, 1)
    if (not isinstance(references, list) or not references or len(references) > 8 or
            any(not isinstance(r, list) or len(r) < 2 or not _id(r[1], MEDIA) for r in references)):
        raise UnsupportedFlowPayload('request_reference_shape')
    return {'rpc_id': REFERENCE_RPC, 'project_id': project_id,
            'input_media_ids': [r[1] for r in references]}


def rpc_payload(raw, rpc_id):
    """Reject incomplete framing, duplicate calls, RPC errors and missing payloads."""
    docs, meta = decode_transport(raw, 'text/plain', direction='response')
    if meta.get('decode_error') or meta.get('partial') or meta.get('truncated'):
        raise UnsupportedFlowPayload('response_framing')
    matches = [];rows=[]
    for _, doc, _ in docs:
        if not isinstance(doc, list):
            raise UnsupportedFlowPayload('response_container')
        for row in doc:
            if not isinstance(row, list) or not row:
                continue
            rows.append(row)
            if row[0] == 'er':
                raise UnsupportedFlowPayload('rpc_error_envelope')
            if row[0] == 'e' and (len(row)<2 or type(row[1])is not int or row[1]!=4):
                raise UnsupportedFlowPayload('rpc_transport_marker_unknown')
            if row[0] == 'wrb.fr' and len(row) > 1 and row[1] == rpc_id:
                matches.append(row)
    if len(matches) != 1:
        raise UnsupportedFlowPayload('response_rpc_count')
    row = matches[0]
    if len(row)>5 and row[2] is None and row[5]:
        raise FlowRpcRejected(_rpc_error_details(row[5],rows))
    if len(row) < 3 or row[2] is None or (len(row) > 5 and row[5]):
        raise UnsupportedFlowPayload('rpc_rejected_or_empty')
    payload = json.loads(row[2]) if isinstance(row[2], str) else row[2]
    if not isinstance(payload, list):
        raise UnsupportedFlowPayload('response_payload_type')
    return payload


def media_rows(payload):
    """Two known container layouts. Never use a recursive UUID fallback."""
    choices = []
    for index in (3, 2):
        if len(payload) > index and isinstance(payload[index], list) and payload[index]:
            rows = payload[index]
            if all(isinstance(row, list) and row and _id(row[0], MEDIA) for row in rows):
                choices.append(rows)
    if len(choices) != 1:
        raise UnsupportedFlowPayload('media_rows_ambiguous_or_missing')
    return choices[0]


def submitted_media(payload, project_id):
    rows = media_rows(payload)
    if len(rows) != 1:
        raise UnsupportedFlowPayload('submit_output_count')
    row = rows[0]
    if len(row) < 3 or row[1] != project_id or not _id(row[2]):
        raise UnsupportedFlowPayload('submit_identity_shape')
    return {'media_id': row[0], 'project_id': row[1], 'workflow_id': row[2]}


def media_status(payload, identity):
    rows = media_rows(payload)
    matching = [row for row in rows if row[0] == identity['media_id']]
    if len(matching) != 1:
        raise UnsupportedFlowPayload('status_media_mismatch')
    row = matching[0]
    if _at(row, 1) != identity['project_id'] or _at(row, 2) != identity['workflow_id']:
        raise UnsupportedFlowPayload('status_project_or_workflow_mismatch')
    status = _at(row, 5, 8)
    code = _at(status, 0)
    if type(code) is not int or code not in (1, 2, 3, 4, 5):
        raise UnsupportedFlowPayload('status_code_unknown')
    result = {'state': 'success' if code == 3 else 'failed' if code in (4, 5) else 'pending',
              'status_code': code}
    if code in (4, 5):
        try:
            reason = _at(status, 1, 1)
            if isinstance(reason, str) and ERROR_CODE.fullmatch(reason):
                result['failure_code'] = reason
        except UnsupportedFlowPayload:
            pass
    return result


def checked_video_url(url, media_id):
    """A signed URL is transient, tied to the returned media ID and never logged."""
    if not isinstance(url, str) or len(url) > 16384:
        return None
    try:
        u = urlsplit(url)
        if (u.scheme == 'https' and u.hostname == 'flow-content.google' and
                u.port in (None, 443) and not u.username and not u.password and
                not u.fragment and u.path == '/video/' + media_id):
            return url
    except ValueError:
        pass
    return None


def asset_video_url(payload, identity):
    # Verify the response identity before looking for a URL anywhere in its row.
    if len(payload) >= 3 and _id(payload[0], MEDIA) and _id(payload[1]) and _id(payload[2]):
        actual = dict(zip(('media_id', 'project_id', 'workflow_id'), payload[:3]))
    else:
        actual = submitted_media(payload, identity['project_id'])
    if actual != identity:
        raise UnsupportedFlowPayload('asset_identity_mismatch')
    found = set()
    budget = 2000
    def walk(value, depth=0):
        nonlocal budget
        budget -= 1
        if budget < 0 or depth > 12:
            raise UnsupportedFlowPayload('asset_scan_limit')
        if isinstance(value, str):
            url = checked_video_url(value, identity['media_id'])
            if url:
                found.add(url)
        elif isinstance(value, list):
            for item in value:
                walk(item, depth + 1)
    walk(payload)
    if len(found) != 1:
        raise UnsupportedFlowPayload('asset_video_url_missing_or_ambiguous')
    return found.pop()
