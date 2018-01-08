#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Default configurations.
"""

from pymysql.cursors import DictCursor

__author__ = 'ffewi'

configs = {
    'debug': True,
    'db': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'password': '',
        'db': 'mzitu'
    },
    'dbPoolArgs': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'passwd': '',
        'db': 'mzitu',
        'mincached': 5,  # 最小池数
        'maxcached': 20,  # 最大池数
        'use_unicode': False,
        'charset': 'utf8',
        'cursorclass': DictCursor
    },
    'autoCreate': {
        # MZiTu 索引
        'MIndex': True,
        # MZiTu套图信息
        'MPicture': True,
        # 套图组
        'MPictureInfo': True,
        'User': True,
        'Blog': True,
        'Comment': True,
        # 漫画台 所有漫画
        'CIndexAll': True,
        # 漫画简介页
        'CComicInfo': True,
        # 漫画章节
        'CComicPicture': True,
        # 漫画图
        'CComicSectionPic': True,
        # 日志记录表
        'ProcessMessage': True

    },
    # 防盗链解决方法控制
    'referrer': {
        'MHT': False,
        'MZT': False,
    },

    'session': {
        'secret': 'habit'
    }
}
