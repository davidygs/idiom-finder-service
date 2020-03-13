import random

from locust import TaskSet, HttpLocust, between

file_path = 'data/chinese_query_words.txt'
query_words = []
with open(file_path) as fp:
    for line in fp:
        query_words += [line.strip()]


def query(l):
    l.client.get("/?query={}".format(random.choice(query_words)), name='query')


class UserBehavior(TaskSet):
    tasks = {query: 1}


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    wait_time = between(1.0, 2.0)
