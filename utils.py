import json
import logging
from exceptions import FetchError


async def fetch(session, url):
    async with session.get(url) as response:
        logging.getLogger('aiohttp.client').info(f'Request {url}')
        data = json.loads(await response.text())
        if not response.status == 200:
            raise FetchError(code=response.status, data=data)
        if not data:
            raise FetchError(code=404)
        return data
