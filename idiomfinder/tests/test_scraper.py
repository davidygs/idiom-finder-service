import pkgutil
from typing import List
from unittest.mock import MagicMock, AsyncMock

import pytest
from aiohttp import ClientSession
from pytest import fixture

from idiomfinder.scraper import BaiduScraper


@fixture
def baidu_scraper():
    return BaiduScraper()


@fixture
def no_results_page():
    p = pkgutil.get_data('idiomfinder.tests', 'data/empty_search_page.html')
    return p.decode('gbk')


@fixture
def normal_results_page():
    p = pkgutil.get_data('idiomfinder.tests', 'data/normal_results_page.html')
    return p.decode('gbk')


@fixture
def normal_search_page():
    p = pkgutil.get_data('idiomfinder.tests', 'data/normal_search_page.html')
    return p.decode('gbk')


def _create_session_mock(mocker, side_effect_htmls: List[str]):
    mock_session = MagicMock(ClientSession)
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value = mock_session

    session_class = mocker.patch('idiomfinder.scraper.aiohttp.ClientSession')
    session_class.return_value = mock_session

    mock_text = AsyncMock()
    mock_text.side_effect = side_effect_htmls

    mock_session.text = mock_text

    return mock_session


@pytest.mark.asyncio
async def test_empty_results_should_retry(baidu_scraper, no_results_page, normal_search_page, mocker):
    side_effect_htmls = [
        no_results_page,
        no_results_page,
        normal_search_page
    ]
    mock_session = _create_session_mock(mocker, side_effect_htmls)

    mock_process_post = mocker.patch('idiomfinder.scraper.BaiduScraper._process_post')
    mock_process_post.return_value = ['沉鱼落雁']

    results = await baidu_scraper.scrape_idioms('美丽')
    assert mock_session.get.call_count == 3
    assert mock_process_post.call_count == 10
    assert len(results) == 1
    assert results[0][0] == '沉鱼落雁'
    assert results[0][1] == 10


@pytest.mark.asyncio
async def test_empty_result_should_return_empty_list(baidu_scraper, no_results_page, mocker):
    baidu_scraper.retries = 1
    side_effect_htmls = [
        no_results_page,
        no_results_page,
    ]
    mock_session = _create_session_mock(mocker, side_effect_htmls)
    results = await baidu_scraper.scrape_idioms('美丽')
    assert mock_session.get.call_count == 2
    assert len(results) == 0


@pytest.mark.asyncio
async def test_normal_results_should_be_extracted(baidu_scraper, normal_search_page, normal_results_page, mocker):
    side_effect_htmls = [
        normal_search_page,
        normal_results_page,  # one page will be scraped
        '', '', '', '', '', '', '', '', ''  # fake the rest of the results page
    ]
    mock_session = _create_session_mock(mocker, side_effect_htmls)
    results = await baidu_scraper.scrape_idioms('美丽')
    assert mock_session.get.call_count == 11
    assert len(results) == 25
