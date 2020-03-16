import asyncio
import os

from sanic import Sanic
from sanic.log import logger
from sanic.response import json, HTTPResponse
from sanic_cors import CORS

from idiomfinder.scraper import IdiomScraper

app = Sanic(name='idiom')
CORS(app)
scraper = None


async def init(_):
    global scraper
    scraper = await IdiomScraper.create()


@app.route("/")
async def get_idioms(request):
    if 'query' not in request.args:
        return HTTPResponse(status=400, body='invalid query')

    query = ''.join(request.args['query'])
    if len(query) > 15:
        return HTTPResponse(status=400, body='query too long')

    try:
        res = await scraper.scrape_idioms(query)
        return json([{'idiom': r[0], 'score': r[1]} for r in res], ensure_ascii=False)
    except Exception as e:
        logger.exception(e)
        return HTTPResponse(status=503)


@app.route('/health')
async def health_check(request):
    return json({'status': 'success'})


if __name__ == "__main__":
    logger.setLevel(os.getenv('SANIC_LOGGING_LEVEL', 'INFO'))
    app.add_task(init)
    app.run(host="0.0.0.0", access_log=False)
