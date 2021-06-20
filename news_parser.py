#!/usr/bin/env python
import json
from constants import faculties as fa
from bs4 import BeautifulSoup as BS
from my_utils import req_post


class Post:
    def __init__(self):
        self.id: str = ''
        self.title: str = ''
        self.link: str = ''

    def __setattr__(self, key, value):
        if not value or not isinstance(value, str):
            value = ''
        self.__dict__[key] = value


class Posts:
    def __init__(self):
        self.posts = []

    def add(self, post: Post):
        self.posts.append(post)

    def __getitem__(self, item):
        return self.posts[item]

    def __bool__(self):
        return bool(self.posts)


def parse_1():
    req = req_post("http://web.kpi.kharkov.ua/cit/uk/", 'GET')
    html = BS(req.content, 'html.parser')
    posts = Posts()
    for element in html.select(".post-row"):
        for item in element.select('article'):
            post = Post()
            post.id = item.get("id")
            post.title = item.find('a').get("title")
            post.link = item.find('a').get("href")
            posts.add(post)
    return posts


def parse_2():
    req = req_post("http://web.kpi.kharkov.ua/if/uk/", 'GET')
    html = BS(req.content, 'html.parser')
    posts = Posts()
    for element in html.select(".post-wrap"):
        for item in element.select('.post-box'):
            post = Post()
            post.id = item.get("id")
            post.title = item.find('a').text
            post.link = item.find('a').get("href")
            posts.add(post)
    return posts


def parse_3():
    req = req_post("http://web.kpi.kharkov.ua/sgt/uk/", 'GET')
    html = BS(req.content, 'html.parser')
    posts = Posts()
    for element in html.select(".post-wrap"):
        for item in element.select('.post-box'):
            post = Post()
            post.id = item.get("id")
            post.title = item.find('a').text
            post.link = item.find('a').get("href")
            posts.add(post)
    return posts


def parse_4():
    req = req_post("http://web.kpi.kharkov.ua/emmb/", 'GET')
    html = BS(req.content, 'html.parser')
    posts = Posts()
    for item in html.select('article'):
        post = Post()
        post.id = item.get("id")
        post.title = item.find('a').get("title")
        post.link = item.find('a').get("href")
        posts.add(post)
    return posts


def parse_5():
    req = req_post("http://web.kpi.kharkov.ua/eee/uk/", 'GET')
    html = BS(req.content, 'html.parser')
    posts = Posts()
    for element in html.select('article'):
        post = Post()
        post.id = element.get("id")
        for item in element.select('.entry-title'):
            post.title = item.text
            post.link = item.find('a').get("href")
            posts.add(post)
    return posts


def parse_news(n, update_last=True):
    """
    :param n: Number of parser or faculty name
    :param update_last: Check for updates
    :return: Posts object
    """
    if not isinstance(n, (str, int)):
        return
    if isinstance(n, str):
        parsers = {fa[0]: parse_1, fa[1]: parse_2, fa[2]: parse_3, fa[3]: parse_4, fa[4]: parse_5}
        if not parsers.get(n):
            return
    else:
        parsers = (parse_1, parse_2, parse_3, parse_4, parse_5)
    posts = parsers[n]()
    if not posts:
        return
    if update_last:
        with open('news_posts.json', 'r') as f:
            data = json.load(f)
        if data[n] == posts[0].id:
            return
        data[n] = posts[0].id
        with open('news_posts.json', 'w') as f:
            json.dump(data, f)
    return posts
