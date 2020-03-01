import asyncio

from aiohttp import ClientError

from idiomfinder.main import app


def test_get_idioms_should_return_200(mocker):
    async def callback(kw):
        return [('沉鱼落雁', 3)]

    scraper = mocker.patch('idiomfinder.main.scraper')
    scraper.scrape_idioms.side_effect = callback
    request, response = app.test_client.get('/?query=美丽')
    assert response.status == 200
    assert response.json[0][0] == '沉鱼落雁'


def test_baidu_timeout_should_return_503(mocker):
    async def sleep(kw):
        await asyncio.sleep(3)

    scraper = mocker.patch('idiomfinder.main.scraper')
    scraper.scrape_idioms.side_effect = sleep
    app.config.RESPONSE_TIMEOUT = 1  # deliberately timing out
    request, response = app.test_client.get('/?query=美丽')
    assert response.status == 503


def test_baidu_connection_error_should_return_503(mocker):
    scraper = mocker.patch('idiomfinder.main.scraper')
    scraper.scrape_idioms.side_effect = ClientError()
    request, response = app.test_client.get('/?query=美丽')
    assert response.status == 503


def test_health_should_return_200():
    request, response = app.test_client.get('/health')
    assert response.status == 200


def test_long_query_should_return_400():
    request, response = app.test_client.get('/?query=美丽美丽美丽美丽美丽美丽美丽美丽')
    assert response.status == 400
