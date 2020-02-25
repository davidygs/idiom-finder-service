from sanic import Sanic
from sanic.response import json

from idiomfinder.scraper import BaiduScraper

app = Sanic(name='idiom')
scraper = BaiduScraper()


@app.route("/")
async def get_idioms(request):
    kw = ''.join(request.args['kw'])
    res = await scraper.scrape_idioms(kw)
    return json(res, ensure_ascii=False)


@app.route('/health')
async def health_check(request):
    return json({'status': 'success'})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, workers=2)
