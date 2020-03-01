from sanic import Sanic
from sanic.log import logger
from sanic.response import json, HTTPResponse
from sanic_cors import CORS

from idiomfinder.scraper import BaiduScraper

app = Sanic(name='idiom')
CORS(app)

scraper = BaiduScraper()


@app.route("/")
async def get_idioms(request):
    query = ''.join(request.args['query'])
    if len(query) > 15:
        return HTTPResponse(status=400, body='query too long')

    try:
        res = await scraper.scrape_idioms(query)
        return json(res, ensure_ascii=False)
    except Exception as e:
        logger.exception(e)
        return HTTPResponse(status=503)


@app.route('/health')
async def health_check(request):
    return json({'status': 'success'})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
