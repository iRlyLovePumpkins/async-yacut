import asyncio
import os

import aiohttp
from dotenv import load_dotenv

API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
PUBLISH_URL = f'{API_HOST}{API_VERSION}/disk/resources/publish'
RESOURCE_URL = f'{API_HOST}{API_VERSION}/disk/resources'
REQUEST_UPLOAD_URL = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_LINK_URL = f'{API_HOST}{API_VERSION}/disk/resources/download'

load_dotenv()
DISK_TOKEN = os.environ.get('DISK_TOKEN')

AUTH_HEADERS = {'Authorization': f'OAuth {DISK_TOKEN}'}


async def async_upload_files_to_yandex_disk(files):
    if not files:
        return []
    tasks = []
    async with aiohttp.ClientSession() as session:
        for file in files:
            tasks.append(
                asyncio.ensure_future(
                    upload_file_and_get_url(session, file)
                )
            )
        urls = await asyncio.gather(*tasks)
    return [item for item in urls if item is not None]


async def upload_file_and_get_url(session, file):
    path = f'/{file.filename}'
    params = {'path': path, 'overwrite': 'True'}

    async with session.get(
        REQUEST_UPLOAD_URL, headers=AUTH_HEADERS, params=params
    ) as response:
        data = await response.json()
        upload_url = data.get('href')

    if not upload_url:
        return None

    async with session.put(upload_url, data=file.read()) as response:
        response.raise_for_status()

    async with session.get(
        DOWNLOAD_LINK_URL, headers=AUTH_HEADERS, params={'path': path}
    ) as response:
        data = await response.json()
        download_url = data.get('href')

    if not download_url:
        return None

    return (file.filename, download_url)
