import abc
import asyncio
import itertools
import re
from collections import Counter
from typing import Tuple, List

import aiohttp
import jieba
from bs4 import BeautifulSoup
from sanic.log import logger

from idiomfinder.validator import IdiomValidator


class Scraper:

    @abc.abstractmethod
    async def scrape_idioms(self, kw: str) -> List[Tuple[str, int]]:
        pass


class BaiduScraper(Scraper):

    def __init__(self,
                 validator: IdiomValidator = IdiomValidator(),
                 base_url: str = 'https://zhidao.baidu.com/search?word=形容描写表示关于{}成语',
                 retries: int = 3):
        self.validator = validator
        self.base_url = base_url
        self.retries = retries

    async def scrape_idioms(self, query: str) -> List[Tuple[str, int]]:

        query = self._extract_chinese(query)
        if not query:
            return []

        # TODO need to rotate a list of user agents
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/57.0.2987.110 '
                                 'Safari/537.36'}

        async with aiohttp.ClientSession(headers=headers) as session:
            retries = self.retries
            while retries > -1:
                async with session.get(self.base_url.format(query)) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    html_text = soup.get_text()

                    # TODO needs further investigation
                    # This happens quite often
                    if '抱歉，暂时没有找到' in html_text:
                        retries -= 1
                        logger.warn('Baidu returns no result. Retry.')
                        continue

                    aws = [self._process_post(session, a['href']) for a in soup.find_all('a', class_='ti')]
                    idiom_lists = await asyncio.gather(*aws)
                    return self._reduce(idiom_lists)
        return []

    @staticmethod
    def _extract_chinese(query):
        query = '' if not query else query
        return ''.join(re.findall(r'[\u4e00-\u9fff]+', query))

    async def _process_post(self, session, post_url) -> List[str]:
        async with session.get(post_url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            a = soup.find_all('div', {"class": ["bd", "answer"]})

            return [idiom
                    for it in a
                    for s in it.stripped_strings
                    for idiom in self._extract_idioms(s)]

    def _extract_idioms(self, post_answer: str) -> List[str]:
        res = [it for it in jieba.cut(post_answer, cut_all=False) if self.validator.is_valid(it)]
        return res

    def _reduce(self, idiom_lists: List[List[str]]) -> List[Tuple[str, int]]:
        counter = Counter(itertools.chain(*idiom_lists)).most_common()
        return [(idiom, score) for idiom, score in counter]
