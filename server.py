from aiohttp import web
import aiofiles
import argparse
import asyncio
import os
import logging
from pathlib import Path

INTERVAL_SECS = 1


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


async def archive(request, read_up_bytes=102400):
    archive_hash = request.match_info.get('archive_hash')
    photos_filepath = os.path.join(args.path, archive_hash)
    if not os.path.exists(photos_filepath):
        async with aiofiles.open('404.html', mode='r') as error_file:
            error_contents = await error_file.read()
        raise web.HTTPNotFound(text=error_contents, content_type='text/html')

    response = web.StreamResponse()
    response.headers['Content-Disposition'] = f'attachment; filename={archive_hash}.zip'
    await response.prepare(request)

    process = await asyncio.create_subprocess_exec(
        'zip',
        '-r',
        '-',
        '.',
        stdout=asyncio.subprocess.PIPE,
        cwd=photos_filepath,
    )
    try:
        while True:
            zip_binary = await process.stdout.read(n=read_up_bytes)
            logger.info('Sending archive chunk ...')
            await response.write(zip_binary)
            if args.delay:
                await asyncio.sleep(5)
            if process.stdout.at_eof():
                return response
    except asyncio.CancelledError:
        logger.info('Download was interrupted')
        raise
    finally:
        try:
            process.kill()
            await process.communicate()
            logger.info('Process was killed')
        except ProcessLookupError:
            logger.info('Process has stopped already')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--logging', action='store_true', help='enable logging')
    parser.add_argument('-d', '--delay', action='store_true', help='enable delay')
    parser.add_argument(
        '-p', '--path', type=Path, default='test_photos', help='photos filepath'
    )
    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    if not args.logging:
        logger.disabled = True

    while True:
        if os.path.exists(args.path):
            break
        args.path = input('Invalid directory, please enter correct one: ')

    app = web.Application()
    app.add_routes(
        [
            web.get('/', handle_index_page),
            web.get('/archive/{archive_hash}/', archive),
            web.static('/static', 'static'),
        ]
    )
    web.run_app(app)
