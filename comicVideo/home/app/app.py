#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ffewi'

'''
async web application.
'''

# import logging; logging.basicConfig(level=logging.INFO)

import json
import os
import time
import asyncio
from datetime import datetime

from aiohttp import web
from jinja2 import Environment, FileSystemLoader

from home.app.config import configs
from home.app.coroweb import add_routes, add_static
from home.app.handlers import cookie2user, COOKIE_NAME
from home.app.orm import create_pool, baseLog

logging = baseLog.getLogger('核心启动')


def init_jinja2(app, **kw):
    logging.info('init jinja2...')

    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', '{%'),
        block_end_string=kw.get('block_end_string', '%}'),
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),
        auto_reload=kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env
    logging.info('页面储存位置：%s' % app['__templating__'])
    logging.info('页面解析[jinja2],配置成功！ {%s}' % options)


@asyncio.coroutine
def logger_factory(app, handler):
    @asyncio.coroutine
    def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        # yield from asyncio.sleep(0.3)
        return (yield from handler(request))

    return logger


@asyncio.coroutine
def auth_factory(app, handler):
    @asyncio.coroutine
    def auth(request):
        logging.info('check user: %s %s' % (request.method, request.path))
        request.__user__ = None
        cookie_str = request.cookies.get(COOKIE_NAME)
        if cookie_str:
            user = yield from cookie2user(cookie_str)
            if user:
                logging.info('set current user: %s' % user.email)
                request.__user__ = user
        if request.path.startswith('/auth') and (request.__user__ is None or not request.__user__.admin > 10):
            logging.info('检查用户：%s 检查cookies：%s' % (request.__user__, request.cookies))
            msg = ''
            if request.__user__ is None:
                msg = '用户未登陆,当前[%s -->  %s]请求被拒绝' % (request.path, request.method)
            elif not request.__user__.admin:
                msg = '非管理员用户,当前[%s -->  %s]请求被拒绝' % (request.path, request.method)
            logging.info(msg)
            return web.HTTPFound('/index.html')
            # return web.HTTPFound('/signin')
        return (yield from handler(request))

    return auth


@asyncio.coroutine
def data_factory(app, handler):
    @asyncio.coroutine
    def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = yield from request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = yield from request.post()
                logging.info('request form: %s' % str(request.__data__))
        return (yield from handler(request))

    return parse_data


@asyncio.coroutine
def response_factory(app, handler):
    @asyncio.coroutine
    def response(request):
        logging.info('Response handler...')
        if request is not None:
            if hasattr(request, '_match_info'):
                if hasattr(request._match_info, 'route'):
                    if hasattr(request._match_info.route, 'status'):
                        if request._match_info.route.status == 404:
                            logging.info('请求路径[%s]%s 不存在' % (request.method, request.url))
                            return web.HTTPFound('/404.html')

        r = yield from handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(
                    body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                r['__user__'] = request.__user__
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int):
            #  and t >= 100 and t < 600
            #  return web.Response(t)
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        # default:
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp

    return response


def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


def showtime_filter(t):
    dt = datetime.fromtimestamp(t)
    m = ''
    if dt.minute < 10:
        m = '0' + str(dt.minute)
    else:
        m = str(dt.minute)
    h = ''
    if dt.hour < 10:
        h = '0' + str(dt.hour)
    else:
        h = str(dt.hour)
    s = ''
    if dt.second < 10:
        s = '0' + str(dt.second)
    else:
        s = str(dt.second)
    return u'%s年%s月%s日 %s:%s:%s' % (dt.year, dt.month, dt.day, h, m, s)


def show_views_filter(v):
    if v is None:
        return 0
    else:
        a = []
        num = int(v)
        while num != 0:
            s3 = num % 1000
            num = num // 1000
            a.append(str(s3))
        a.reverse()
        return ','.join(a)


@asyncio.coroutine
def init(loop):
    start_time = time.time()
    yield from create_pool(loop=loop, **configs.db)
    app = web.Application(loop=loop, middlewares=[
        logger_factory, auth_factory, response_factory
    ])

    init_jinja2(app, filters=dict(datetime=datetime_filter, showtime=showtime_filter, views=show_views_filter))
    # init_jinja2(app, filters=dict())
    add_routes(app, 'handlers')
    add_static(app)
    srv = yield from loop.create_server(app.make_handler(), '192.168.1.41', 9001)
    logging.info('server started at http://127.0.0.1:9001...')
    finish_time = time.time()
    logging.info('启动耗时：%s ms' % int((finish_time - start_time)*1000))
    return srv


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

