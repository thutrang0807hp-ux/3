"""Gemini Chat SDK worker. No API key, browser-cookie discovery or automatic resend."""
import asyncio
import base64
import contextlib
import json
import os
import re
from pathlib import Path
import sys
from urllib.parse import urlsplit


def single_send_type(base):
    class SingleSend(base):
        async def _generate(self, *args, **kwargs):
            self._sf_generate_started = True
            self._sf_received_output = False
            async for item in base._generate.__wrapped__(self, *args, **kwargs):
                self._sf_received_output = True
                yield item
    return SingleSend


def error_detail(error, phase):
    # No exception text, URLs, prompts, paths, cookies or raw SDK response in diagnostics.
    error_type = type(error).__name__
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}', error_type):
        error_type = 'Exception'
    status = getattr(error, 'status_code', None)
    if status is None:
        status = getattr(getattr(error, 'response', None), 'status_code', None)
    if status is None:
        match = re.match(r'^Error downloading image: ([1-5][0-9]{2})(?:\s|$)', str(error))
        if match:
            status = int(match.group(1))
    codes = {'initialize': 'GEMINI_INIT_ERROR', 'prepare_references': 'GEMINI_ATTACHMENT_ERROR',
             'upload_or_prepare': 'GEMINI_UPLOAD_ERROR', 'generate': 'GEMINI_GENERATE_ERROR',
             'download_image': 'GEMINI_IMAGE_DOWNLOAD_ERROR', 'read_result': 'GEMINI_RESULT_ERROR'}
    result = {'code': codes.get(phase, 'GEMINI_WORKER_ERROR'), 'phase': phase, 'error_type': error_type}
    if isinstance(status, int) and not isinstance(status, bool) and 100 <= status <= 599:
        result['http_status'] = status
    return result


async def execute(body, client_type=None):
    os.environ['GEMINI_COOKIE_PATH'] = str(Path(body['_workspace']) / 'cookie-cache')
    from gemini_webapi import GeminiClient, GeneratedImage
    from gemini_webapi.exceptions import AuthError, UsageLimitExceededError, ModelInvalidError
    from loguru import logger
    logger.remove()
    import importlib
    importlib.import_module('gemini_webapi.utils.get_access_token').HAS_BC3 = False

    try:
        from .gemini_image_results import image_descriptor, download_existing, find_exact_image
    except ImportError:
        from gemini_image_results import image_descriptor, download_existing, find_exact_image

    cookies = body.get('session', {}).get('cookies', {})
    if not cookies.get('__Secure-1PSID'):
        return {'ok': False, 'accepted': False, 'reason': 'auth'}
    if client_type is None and not callable(getattr(getattr(GeminiClient,'_generate',None),'__wrapped__',None)):
        return {'ok':False,'accepted':False,'reason':'sdk_incompatible','code':'SDK_CONTRACT_MISMATCH'}
    client = (client_type or single_send_type(GeminiClient))(secure_1psid=cookies['__Secure-1PSID'], secure_1psidts=cookies.get('__Secure-1PSIDTS'))
    client.cookies = cookies
    sent = False
    chat = None
    conversation = None
    image_result = None
    phase = 'initialize'
    if client_type is None:
        client._sf_generate_started = False
    try:
        await client.init(timeout=450, auto_refresh=False, auto_close=False, watchdog_timeout=10000, verbose=False)
        if not client._check_account_status() or getattr(client, '_cookie_source', '') == 'Guest' or not client.access_token:
            raise AuthError('account required')
        models = [{'id': m.model_name, 'name': m.model_name} for m in (client.list_models() or [])]
        if body['operation'] == 'check':
            answer = {'ok': True, 'models': models}
        elif body['operation'] == 'receive_image':
            phase = 'download_image'
            image_result = body['image_result']
            image = await find_exact_image(client, image_result)
            image_result = image_descriptor(image, image_result.get('metadata'))
            variant = await download_existing(image, client, body['output'])
            answer = {'ok': True, 'image': True, 'download_variant': variant, 'image_result': image_result}
        else:
            model = body.get('model') or None
            if model and model not in {m['id'] for m in models}:
                return {'ok': False, 'accepted': False, 'reason': 'input'}
            phase = 'prepare_references'
            refs = []
            for index, media in enumerate(body.get('references', [])):
                ext = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp',
                       'video/mp4': '.mp4', 'video/webm': '.webm', 'video/quicktime': '.mov'}[media['mime_type']]
                path = Path(body['_workspace']) / (str(index) + ext)
                path.write_bytes(base64.b64decode(media['data'], validate=True))
                refs.append(path)
            # Images for one project/account continue a persistent SDK ChatSession.
            # Text analysis/writing stays stateless and cannot pollute this image chat.
            if body.get('conversation') is not None:
                try:
                    from .gemini_conversations import valid_metadata
                except ImportError:
                    from gemini_conversations import valid_metadata
                metadata = body['conversation'].get('metadata')
                if metadata is not None and not valid_metadata(metadata):
                    return {'ok': False, 'accepted': False, 'reason': 'input'}
                chat = client.start_chat(metadata=metadata, model=model)
            phase = 'upload_or_prepare'
            sent = True
            response = await (chat.send_message(body['prompt'], files=refs or None) if chat
                              else client.generate_content(body['prompt'], files=refs or None, model=model))
            phase = 'read_result'
            if chat:
                metadata = list(chat.metadata)
                # Fake transports may not update ChatSession.last_output, unlike the SDK.
                if not valid_metadata(metadata):
                    metadata = list(response.metadata)
                    if valid_metadata(metadata) and getattr(response, 'rcid', None):
                        metadata[2:3] = [response.rcid]
                if not valid_metadata(metadata):
                    return {'ok': False, 'accepted': True, 'reason': 'conversation_metadata'}
                conversation = {'metadata': metadata}
            if body.get('kind') == 'image':
                images = [i for i in response.images if isinstance(i, GeneratedImage)]
                if not images:
                    return {'ok': False, 'accepted': True, 'reason': 'no_generated_image', 'conversation': conversation}
                phase = 'download_image'
                image_result = image_descriptor(images[0], (conversation or {}).get('metadata') or list(response.metadata))
                variant = await download_existing(images[0], client, body['output'])
                answer = {'ok': True, 'image': True, 'download_variant': variant, 'image_result': image_result}
            else:
                text = response.text
                if not isinstance(text, str) or not text.strip() or len(text) > 500000:
                    raise ValueError('invalid text')
                answer = {'ok': True, 'text': text}
        if conversation:
            answer['conversation'] = conversation
        answer['session'] = {'cookies': {c.name: c.value for c in client.cookies.jar
                               if c.domain.lstrip('.') == 'google.com' or c.domain.endswith('.google.com')}}
        return answer
    except UsageLimitExceededError:
        # SDK typed error maps Google's explicit usage-limit rejection, not a
        # generic HTTP 429/network error.
        return {'ok': False, 'accepted': True if getattr(client, '_sf_received_output', False) else False, 'reason': 'quota'}
    except AuthError:
        return {'ok': False, 'accepted': sent, 'reason': 'auth'}
    except ModelInvalidError:
        return {'ok': False, 'accepted': sent, 'reason': 'input'}
    except Exception as error:
        if phase == 'upload_or_prepare' and getattr(client, '_sf_generate_started', False):
            phase = 'generate'
        # Only the pinned SingleSend transport can prove generation was never entered.
        not_dispatched = not sent or (client_type is None and not client._sf_generate_started)
        return {'ok': False, 'accepted': False if not_dispatched else None,
                'reason': 'unknown', 'conversation': conversation, **({'image_result': image_result} if image_result else {}), **error_detail(error, phase)}
    finally:
        with contextlib.suppress(Exception):
            await client.close()


if __name__ == '__main__':
    body = json.loads(sys.stdin.buffer.read(45 * 1024**2))
    with contextlib.redirect_stdout(sys.stderr):
        try:
            result = asyncio.run(execute(body))
        except Exception as error:
            result = {'ok': False, 'accepted': False, 'reason': 'unknown', **error_detail(error, 'initialize')}
    sys.stdout.write(json.dumps(result))
