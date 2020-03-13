import pkgutil
from typing import List, Any
from unittest.mock import ANY

import pytest
from aiohttp import ClientResponseError, ServerTimeoutError
from pytest import fixture

import idiomfinder
from idiomfinder.scraper import BASE_URL, IdiomScraper

pytestmark = pytest.mark.asyncio


@fixture
async def idiom_scraper():
    idiom_scraper = await IdiomScraper.create()
    return idiom_scraper


@fixture
def no_results_page():
    p = pkgutil.get_data('idiomfinder.tests', 'data/empty_search_page.html')
    return p.decode('gbk')


@fixture
def normal_post_page():
    p = pkgutil.get_data('idiomfinder.tests', 'data/normal_post_page.html')
    return p.decode('gbk')


@fixture
def normal_search_page():
    p = pkgutil.get_data('idiomfinder.tests', 'data/normal_search_page.html')
    return p.decode('gbk')


def _create_get_html_mock(mocker, side_effects: List[Any]):
    mock = mocker.patch('idiomfinder.scraper._get_html')
    mock.side_effect = side_effects
    return mock


async def test_empty_results_should_retry(idiom_scraper, no_results_page, normal_search_page, mocker):
    side_effects = [
                       no_results_page,
                       normal_search_page
                   ] + [''] * 10
    mock = _create_get_html_mock(mocker, side_effects)
    await idiom_scraper.scrape_idioms('美丽')
    assert mock.call_count == 12


async def test_empty_result_should_return_empty_list(idiom_scraper, no_results_page, mocker):
    side_effects = [
        no_results_page,
        no_results_page,
        no_results_page,
        no_results_page,
    ]
    mock = _create_get_html_mock(mocker, side_effects)
    results = await idiom_scraper.scrape_idioms('美丽')
    assert mock.call_count == 4  # original fetch + 3 retries (by default)
    assert len(results) == 0


async def test_normal_results_should_be_extracted(idiom_scraper, normal_search_page, normal_post_page, mocker):
    side_effects = [
                       normal_search_page,
                       normal_post_page,  # one page will be scraped
                   ] + [''] * 9  # fake the rest of the results page
    mock = _create_get_html_mock(mocker, side_effects)
    results = await idiom_scraper.scrape_idioms('美丽')
    assert mock.call_count == 11
    assert len(results) == 25


async def test_invalid_query_should_return_empty_result(idiom_scraper, mocker):
    mock = _create_get_html_mock(mocker, [])

    results = await idiom_scraper.scrape_idioms('')
    assert len(results) == 0

    results = await idiom_scraper.scrape_idioms('non-chinese query')
    assert len(results) == 0

    assert mock.call_count == 0


async def test_non_chinese_query_should_be_stripped(idiom_scraper, mocker):
    mock = _create_get_html_mock(mocker, [''])
    await idiom_scraper.scrape_idioms('  non-chinese query 天气 foo 晴朗 bar  ')
    mock.assert_called_once_with(ANY, BASE_URL.format('天气晴朗'))


async def test_search_page_fetch_failure_should_raise(idiom_scraper, mocker):
    side_effects = [ClientResponseError(None, ()), ServerTimeoutError]
    _create_get_html_mock(mocker, side_effects)

    with pytest.raises(ClientResponseError):
        await idiom_scraper.scrape_idioms('美丽')

    with pytest.raises(ServerTimeoutError):
        await idiom_scraper.scrape_idioms('美丽')


async def test_post_page_fetch_failure_should_ignore(idiom_scraper, normal_search_page, normal_post_page, mocker):
    # 7 successful post fetches + 3 failed post fetches
    side_effects = [normal_search_page] + \
                   [normal_post_page] * 7 + \
                   [ClientResponseError(None, ())] * 3
    _create_get_html_mock(mocker, side_effects)

    spy = mocker.spy(idiomfinder.scraper, '_process_post')
    await idiom_scraper.scrape_idioms('美丽')
    assert spy.call_count == 7
