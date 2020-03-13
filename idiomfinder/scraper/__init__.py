import asyncio
import itertools
import os
import re
from collections import Counter
from typing import Tuple, List

import jieba
from aiohttp import ClientTimeout, ClientResponseError
from aiohttp_retry import RetryClient
from bs4 import BeautifulSoup
from sanic.log import logger

from idiomfinder.validator import IdiomValidator

BASE_URL = 'https://zhidao.baidu.com/search?word=形容描写表示关于{}成语'
RESPONSE_ENCODING = 'gbk'
CLIENT_TIMEOUT = os.getenv('CLIENT_TIMEOUT', 10)
RETRIES = 3

validator = IdiomValidator()


async def _get_html(retry_client, url) -> str:
    async with retry_client.get(
            url,
            retry_attempts=RETRIES,
            retry_exceptions=[ClientResponseError, TimeoutError]
    ) as rs:
        return await rs.text(RESPONSE_ENCODING)


def _extract_post_urls(base_html):
    x = [a['href'] for a in BeautifulSoup(base_html, 'html.parser').find_all('a', class_='ti')]
    return x


async def _fetch_base_html(retry_client, query):
    # TODO needs further investigation as it happens quite often
    base_html, retries = '', RETRIES
    while retries > -1:
        base_html = await _get_html(retry_client, BASE_URL.format(query))

        def is_empty():
            soup = BeautifulSoup(base_html, 'html.parser')
            html_text = soup.get_text()
            return '抱歉，暂时没有找到' in html_text

        if is_empty():
            retries -= 1
            logger.warn('Baidu returns no result. Retry.')
            continue

        break

    return base_html


def _extract_chinese(query):
    query = '' if not query else query
    return ''.join(re.findall(r'[\u4e00-\u9fff]+', query))


def _process_post(post_html) -> List[str]:
    """
    Extract all idioms out of a post html
    :param post_html:
    :return:
    """

    def extract_idioms(post_answer: str) -> List[str]:
        res = [it for it in jieba.cut(post_answer, cut_all=False) if validator.is_valid(it)]
        return res

    soup = BeautifulSoup(post_html, 'html.parser')
    a = soup.find_all('div', {"class": ["bd", "answer"]})

    return [idiom
            for it in a
            for s in it.stripped_strings
            for idiom in extract_idioms(s)]


def _reduce(idiom_lists: List[List[str]]) -> List[Tuple[str, int]]:
    counter = Counter(itertools.chain(*idiom_lists)).most_common()
    return [(idiom, score) for idiom, score in counter]


async def scrape_idioms(query: str) -> List[Tuple[str, int]]:
    query = _extract_chinese(query)
    if not query:
        return []

    retry_client = RetryClient(
        raise_for_status=True,  # raise exception if response status >= 400
        timeout=ClientTimeout(total=CLIENT_TIMEOUT)  # set a timeout value
    )
    post_html_list = []
    async with retry_client:
        try:
            base_html = await _fetch_base_html(retry_client, query)
            aws = [_get_html(retry_client, url) for url in _extract_post_urls(base_html)]
            fetch_results = await asyncio.gather(*aws, return_exceptions=True)
            exceptions = [it for it in fetch_results if isinstance(it, Exception)]
            post_html_list = [it for it in fetch_results if not isinstance(it, Exception)]
            if exceptions:
                logger.error(f'Exceptions encountered {[repr(e) for e in exceptions]}')
        except Exception as e:
            logger.error(repr(e))
            raise e

    return _reduce([_process_post(post_html) for post_html in post_html_list])
