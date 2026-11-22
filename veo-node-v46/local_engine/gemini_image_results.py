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


async def download_existing(image, client, output):
    """Two bounded file downloads, never a second generation. Expose actual variant."""
    original = image.url
    output = Path(output)
    try:
        await image.save(path=str(output.parent), filename=output.name, client=client.client, full_size=True, verbose=False)
        return 'full-size'
    except Exception:
        # SDK mutates the URL when requesting full-size. Restore before using its
        # standard rendition of the SAME generated image, not a resized local fake.
        output.unlink(missing_ok=True)
        image.url = original
        await image.save(path=str(output.parent), filename=output.name, client=client.client, full_size=False, verbose=False)
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
