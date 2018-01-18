#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Models for user, blog, comment.
'''

__author__ = 'ffewi'

import time
import uuid
import datetime

from home.app.orm import *
from home.app.config import configs


# @asyncio.coroutine
# def test():
#     yield from create_pool(loop=loop, **configs.db)
#     # rs = yield from base.findAll()
#     # r1 = yield from base.find(1)
#     # print(rs)
#     logging.info('初始化资源池')
#
#
# loop = asyncio.get_event_loop()
#
# loop.run_until_complete(test())

AUTO_CREATE = configs.autoCreate


def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)


def str2time(str_time, format_str='%Y-%m-%d'):
    if str_time is None or str_time.strip() == '':
        return time.time()
    t = time.strptime(str_time, format_str)
    y, m, d, h, mm, s = t[0:6]
    times = datetime.datetime(y, m, d, h, mm, s).timestamp()
    return times


# ===================================================m zi tu对象=========================================
# M: m_zi_tu
# 索引
class MIndex(Model):
    __table__ = 'mzt_index_page'
    __autoCreate__ = AUTO_CREATE.get('MIndex', False)

    id = StringField(name='唯一主键', primary_key=True, default=next_id, ddl='varchar(50)')
    page_title = StringField(name='套图标题', ddl='varchar(255)')
    page_url = StringField(name='套图地址', ddl='varchar(500)')
    url_order = IntegerField(name='地址序号')


# 图组信息，并且含有第一张图片地址
class MPicture(Model):
    __table__ = 'mzt_pic_page'
    __autoCreate__ = AUTO_CREATE.get('MPicture', False)

    id = StringField(name='唯一主键', primary_key=True, default=next_id, ddl='varchar(50)')
    views = IntegerField(name='浏览量')
    pic_type = StringField(name='图类型', ddl='varchar(50)')
    pic_title = StringField(name='图片标题', ddl='varchar(255)')
    pic_url = StringField(name='图片地址', ddl='varchar(500)')
    created_at = FloatField(name='发布时间', default=time.time)
    index_id = StringField(name='索引地址主键')


# 套图地址
class MPictureInfo(Model):
    __table__ = 'mzt_pic_group'
    __autoCreate__ = AUTO_CREATE.get('MPictureInfo', False)

    id = StringField(name='唯一主键', primary_key=True, default=next_id, ddl='varchar(50)')
    img_order = IntegerField(name='图片序号')
    img_url = StringField(name='图片地址', ddl='varchar(500)')
    group_id = StringField(name='套图图组id', ddl='varchar(50)')

# ===================================================m zi tu对象结束=========================================


# ===================================================日志对象=========================================
class User(Model):
    __table__ = 'users'
    __autoCreate__ = AUTO_CREATE.get('User', False)

    id = StringField(name='唯一主键', primary_key=True, default=next_id, ddl='varchar(50)')
    email = StringField(name='邮箱', ddl='varchar(50)')
    passwd = StringField(name='密码', ddl='varchar(50)')
    admin = BooleanField(name='是否管理员', )
    name = StringField(name='姓名', ddl='varchar(50)')
    image = StringField(name='头像', ddl='varchar(500)')
    created_at = FloatField(name='创建时间', default=time.time)


class Blog(Model):
    __table__ = 'blogs'
    __autoCreate__ = AUTO_CREATE.get('Blog', False)

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    tags = StringField(ddl='varchar(100)')
    content = TextField()
    created_at = FloatField(default=time.time)


class Comment(Model):
    __table__ = 'comments'
    __autoCreate__ = AUTO_CREATE.get('Comment', False)

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time)

# ===================================================日志对象结束=========================================

# ===================================================漫画台对象  =========================================
# C :comic

# 所有漫画索引


class CIndexAll(Model):
    __table__ = 'mht_index_all'
    __autoCreate__ = AUTO_CREATE.get('CIndexAll', False)

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    name = StringField(name='漫画名称', ddl='varchar(50)')
    type = StringField(name='漫画类型', ddl='varchar(50)')
    status = StringField(name='状态', ddl='varchar(50)')
    plot = StringField(name='剧情', ddl='varchar(255)')
    pic = StringField(name="封面图地址", ddl='varchar(500)')
    commons = StringField(name="更新章节", ddl='varchar(50)')
    index_url = StringField(name='导航页地址', ddl='varchar(500)')  # 更新的时候使用


# 漫画简介页
class CComicInfo(Model):
    __table__ = 'mht_comic_info'
    __autoCreate__ = AUTO_CREATE.get('CComicInfo', False)

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    name = StringField(name='漫画名称', ddl='varchar(50)')
    type = StringField(name='漫画类型', ddl='varchar(50)')
    author = StringField(name='漫画作者', ddl='varchar(50)')
    status = StringField(name='状态', ddl='varchar(50)')
    up_time = FloatField(name='更新时间')
    plot = StringField(name='漫画简介', ddl='varchar(500)')
    share_times = IntegerField(name='分享次数')
    pic_url = StringField(name='图片地址', ddl='varchar(500)')
    pic_title = StringField(name='图片悬浮提示', ddl='varchar(50)')
    index_id = StringField(name='索引页id', ddl='varchar(50)')


# 漫画 章节信息
class CComicPicture(Model):
    __table__ = 'mht_comic_pic'
    __autoCreate__ = AUTO_CREATE.get('CComicPicture', False)

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    sort_order = IntegerField(name='页号-也是排序')
    href = StringField(name='相对请求路径', ddl='varchar(500)')
    title = StringField(name='悬浮标题', ddl='varchar(50)')
    comic_id = StringField(name='漫画id', ddl='varchar(50)')


# 漫画 浏览时的每章节图片
class CComicSectionPic(Model):
    __table__ = 'mht_comic_section_pic'
    __autoCreate__ = AUTO_CREATE.get('CComicSectionPic', False)

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    sort_order = IntegerField(name='第几张图-也是排序')
    pic_url = StringField(name='图片地址', ddl='varchar(500)')
    section_id = StringField(name='对应的章节id', ddl='varchar(50)')

# ===================================================漫画台对象结束========================================

# ===================================================业务日志开始========================================


# 操作日志消息
class ProcessMessage(Model):
    __table__ = 'process_message'
    __autoCreate__ = AUTO_CREATE.get('ProcessMessage', False)

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    content = StringField(name='消息内容', ddl='varchar(500)')
    message_type = StringField(name='消息类型', ddl='varchar(50)')
    trans_id = StringField(name='流程id', ddl='varchar(50)')  # 标志一组信息
    status = StringField(name="执行状态", ddl='varchar(50)')
    message_order = IntegerField(name="执行顺序")
    created_at = FloatField(name='创建时间', default=time.time)

# ===================================================业务日志结束========================================
