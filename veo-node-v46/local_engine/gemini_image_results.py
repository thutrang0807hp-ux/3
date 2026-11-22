"""Download existing generated images only. Descriptors must be kept in the encrypted vault."""
from pathlib import Path
from urllib.parse import urlsplit


def image_descriptor(image, metadata=None):
    url = str(image.url)
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or not (parts.hostname == 'googleusercontent.com' or parts.hostname.endswith('.googleusercontent.com')) or parts.port not in (None,443) or parts.username or parts.password or len(url) > 16000:
        raise ValueError('invalid generated image host')
    data = {'url': url}
    for key in ('cid', 'rid', 'rcid', 'image_id'):
        value = getattr(image, key, '')
        if isinstance(value, str) and len(value) <= 100000:
            data[key] = value
    return {'image': data, 'metadata': metadata}


class ImageDownloadError(Exception):
    def __init__(self, status=None):
        super().__init__('Generated image transfer failed')
        self.status_code = status


async def download_provided(image, client, output):
    """Use the exact provider URL: never append size suffixes to signed query strings."""
    import asyncio
    image_descriptor(image)
    response = await asyncio.wait_for(client.client.get(str(image.url), headers={'Referer':'https://gemini.google.com/'}), 45)
    status = getattr(response, 'status_code', None)
    if status != 200:
        raise ImageDownloadError(status)
    data = response.content
    if not isinstance(data, bytes) or not 0 < len(data) <= 24 * 1024**2:
        raise ImageDownloadError()
    if not (data.startswith(b'\x89PNG\r\n\x1a\n') or data.startswith(b'\xff\xd8\xff') or (data[:4] == b'RIFF' and data[8:12] == b'WEBP')):
        raise ImageDownloadError()
    Path(output).write_bytes(data)
    return 'provided'


async def download_existing(image, client, output):
    """Downloads only this image. Preserve signed URLs; no second generation."""
    import asyncio
    original = str(image.url)
    output = Path(output)
    try:
        return await download_provided(image, client, output)
    except Exception as original_error:
        output.unlink(missing_ok=True)
        if urlsplit(original).query:
            # If the original link expired, the SDK's authenticated image RPC
            # can mint a new link for this exact cid/rid/rcid/image_id. Permit
            # that route but block its fallback that appends sizes to a query.
            if not all(getattr(image, key, None) for key in ('client_ref','cid','rid','rcid','image_id')):
                raise
            failure = original_error
            from types import SimpleNamespace
            class SignedSession:
                def __init__(self):
                    self.provided = {original}
                async def get(self, url, **kwargs):
                    candidate = str(url)
                    for known in self.provided:
                        changed = {known+'=s1024-rj', known+'=s2048-rj', known.replace('=s1024-rj','=s2048-rj'), known.replace('=s2048-rj','=s1024-rj')}
                        if candidate == original or (candidate != known and candidate in changed):
                            raise failure
                    image_descriptor(SimpleNamespace(url=candidate))
                    if urlsplit(candidate).query:
                        self.provided.add(candidate)
                    return await client.client.get(url, **kwargs)
            try:
                image.url = original
                await asyncio.wait_for(image.save(path=str(output.parent), filename=output.name, client=SignedSession(), full_size=True, verbose=False), 45)
                return 'full-size'
            finally:
                image.url = original
    try:
        image.url = original
        await asyncio.wait_for(image.save(path=str(output.parent), filename=output.name, client=client.client, full_size=True, verbose=False), 45)
        return 'full-size'
    except Exception:
        output.unlink(missing_ok=True)
        image.url = original
        await asyncio.wait_for(image.save(path=str(output.parent), filename=output.name, client=client.client, full_size=False, verbose=False), 30)
        return 'standard'


async def find_exact_image(client, pointer):
    from gemini_webapi import GeneratedImage
    metadata = pointer.get('metadata')
    # Re-read only the exact old turn; never use latest-chat fallback.
    if isinstance(metadata, list) and len(metadata) >= 2 and isinstance(metadata[0], str) and metadata[0].startswith('c_') and isinstance(metadata[1], str) and metadata[1].startswith('r_'):
        try:
            history = await client.read_chat(metadata[0], limit=30)
        except Exception:
            if not isinstance(pointer.get('image'), dict):
                raise
            history = None
        for turn in (history.turns if history else []):
            response = turn.model_output
            if turn.role != 'model' or response is None or response.metadata[:2] != metadata[:2]:
                continue
            candidates = response.candidates
            for index, candidate in enumerate(candidates):
                if len(metadata) > 2 and metadata[2] and candidate.rcid != metadata[2]:
                    continue
                response.chosen = index
                images = [i for i in response.images if isinstance(i, GeneratedImage)]
                if images:
                    return images[0]
    data = pointer.get('image')
    if isinstance(data, dict):
        image = GeneratedImage(**data, title='Generated result', alt='Generated result', client_ref=client)
        image_descriptor(image, metadata)  # host/size validation before network access
        return image
    raise ValueError('exact original generated image unavailable')
