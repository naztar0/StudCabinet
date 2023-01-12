#!/usr/bin/env python
import json
from app.misc import faculties as fa, temp_dir
from bs4 import BeautifulSoup as BS
from app.utils.my_utils import *


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
    req = req_post("http://web.kpi.kharkov.ua/if/uk/", 'GET')
    if not req:
        return
    html = BS(req.content, 'html.parser')
    posts = Posts()
    for element in html.select(".post-wrap"):
        for item in element.select('.post-box'):
            if not (item.get("id") and item.find('a')):
                continue
            post = Post()
            post.id = item.get("id")
            post.title = item.find('a').text
            post.link = item.find('a').get("href")
            posts.add(post)
    return posts


def parse_2():
    req = req_post("http://web.kpi.kharkov.ua/sgt/uk/", 'GET')
    if not req:
        return
    html = BS(req.content, 'html.parser')
    posts = Posts()
    for element in html.select(".post-wrap"):
        for item in element.select('.post-box'):
            if not (item.get("id") and item.find('a')):
                continue
            post = Post()
            post.id = item.get("id")
            post.title = item.find('a').text
            post.link = item.find('a').get("href")
            posts.add(post)
    return posts


def parse_3():
    req = req_post("http://web.kpi.kharkov.ua/emmb/", 'GET')
    if not req:
        return
    html = BS(req.content, 'html.parser')
    posts = Posts()
    for item in html.select('table'):
        if not item.find('a'):
            continue
        post = Post()
        post.title = item.find('strong').text.strip()
        post.link = item.find('a').get("href")
        post.id = post.link
        posts.add(post)
    return posts


def parse_4():
    req = req_post("http://web.kpi.kharkov.ua/eee/", 'GET')
    if not req:
        return
    html = BS(req.content, 'html.parser')
    posts = Posts()
    for element in html.select('article'):
        post = Post()
        post.id = element.get("id")
        for item in element.select('.entry-title'):
            if not (element.get("id") and item.find('a')):
                continue
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
    parsers = {fa[0]: parse_1, fa[1]: parse_2, fa[2]: parse_3, fa[3]: parse_4}
    if not isinstance(n, (str, int)):
        return
    if isinstance(n, int):
        n: str = fa[n]
    if not parsers.get(n):
        return
    posts = parsers[n]()
    if not posts:
        return
    if update_last:
        filename_posts = temp_dir/'news_posts.json'
        filename_texts = temp_dir/'news_texts.json'
        last_post_id = get_update_json(filename_posts, n)
        if last_post_id == posts[0].id:
            return
        get_update_json(filename_posts, n, posts[0].id)
        news_str = ''
        for i, post in enumerate(posts, 1):
            news_str += f'*{i}.* [{esc_md(post.title)}]({esc_md(post.link)})\n'
            if i == 10: break
        get_update_json(filename_texts, n, news_str)
    return posts
