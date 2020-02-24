import asyncio
import itertools
from collections import Counter
from typing import List, Tuple

import aiohttp
import jieba
from bs4 import BeautifulSoup
from sanic import Sanic
from sanic.response import json

from idiomfinder.idiomchecker.idiom_checker import IdiomChecker

idiom_checker = IdiomChecker()
app = Sanic(name='idiom')
base_url = 'https://zhidao.baidu.com/search?word=形容描写表示关于{}成语'


async def process_post(session, post_url) -> List[str]:
    async with session.get(post_url) as response:
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')
        a = soup.find_all('div', {"class": ["bd", "answer"]})

        return [idiom
                for it in a
                for s in it.stripped_strings
                for idiom in extract_idioms(s)]


def reduce(idiom_lists: List[List[str]]) -> List[Tuple[str, int]]:
    counter = Counter(itertools.chain(*idiom_lists)).most_common()
    return [(idiom, score) for idiom, score in counter]


async def crawl(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            print(f'response received from {url}')
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')

            aws = [process_post(session, a['href']) for a in soup.find_all('a', class_='ti')]
            idiom_lists = await asyncio.gather(*aws)
            return reduce(idiom_lists)


def extract_idioms(post_answer: str) -> List[str]:
    res = [it for it in jieba.cut(post_answer, cut_all=False) if idiom_checker.is_idiom(it)]
    return res


@app.route("/")
async def get_idioms(request):
    kw = ''.join(request.args['kw'])
    res = await crawl(base_url.format(kw))
    return json(res, ensure_ascii=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, workers=2)
