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
    kw = ''.join(request.args['kw'])
    try:
        res = await scraper.scrape_idioms(kw)
        return json(res, ensure_ascii=False)
    except Exception as e:
        logger.exception(e)
        return HTTPResponse(status=503)


@app.route('/health')
async def health_check(request):
    return json({'status': 'success'})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
