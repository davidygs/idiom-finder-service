import abc
import asyncio
import itertools
from collections import Counter
from typing import Tuple, List

import aiohttp
import jieba
from bs4 import BeautifulSoup

from idiomfinder.validator import IdiomValidator


class Scraper:

    @abc.abstractmethod
    async def scrape_idioms(self, kw: str) -> List[Tuple[str, int]]:
        pass


class BaiduScraper(Scraper):

    def __init__(self,
                 validator: IdiomValidator = IdiomValidator(),
                 base_url: str = 'https://zhidao.baidu.com/search?word=形容描写表示关于{}成语'):
        self.validator = validator
        self.base_url = base_url

    async def scrape_idioms(self, kw: str) -> List[Tuple[str, int]]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url.format(kw)) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                aws = [self._process_post(session, a['href']) for a in soup.find_all('a', class_='ti')]
                idiom_lists = await asyncio.gather(*aws)
                return self._reduce(idiom_lists)

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


if __name__ == '__main__':
    scraper = BaiduScraper()
    idioms = asyncio.run(scraper.scrape_idioms('美丽'))
    print(idioms)
