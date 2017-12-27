#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

' url handlers '

import hashlib
import random
import re

from aiohttp import web

from home.app import markdown2
from home.app.apis import *
# from home.app.config import configs
from home.app.coroweb import get, post
from home.app.t_manhuatai import *
from home.app.t_monitor import *
from home.app.tool_manhuatai import MHuaTai

# from home.app.models import *


COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret


def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()


def check_super_admin(request):
    if request.__user__ is None or not request.__user__.admin == 2:
        if request is None or request.__user__ is None:
            name = '匿名用户'
        else:
            name = request.__user__.name
        return {'status': 'fail', 'err': '系统提示：【%s：权限不够，请联系超级管理员！】' % name}
    return False


def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p


def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)


def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'),
                filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)


@asyncio.coroutine
def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = yield from User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None


@get('/notes.html')
def index(*, page='1'):
    page_index = get_page_index(page)
    num = yield from Blog.findNumber('count(id)')
    page = Page(num, page_index=page_index, page_url='/notes.html?page=')
    if num == 0:
        blogs = []
    else:
        blogs = yield from Blog.findAll(orderBy='created_at desc', limit=(page.offset, page.limit))
    return {
        '__template__': 'h_blogs.html',
        'page': page,
        'blogs': blogs
    }


@get('/blog/{id}')
def get_blog(id):
    blog = yield from Blog.find(id)
    comments = yield from Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'h_blog.html',
        'blog': blog,
        'comments': comments
    }


@get('/register')
def register():
    return {
        '__template__': 'h_register.html'
    }


@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }


@post('/api/authenticate')
def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = yield from User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]
    # check passwd:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r


# 管理员 登录 管理--> 跳转界面
@get('/auth/manager.html')
def manage():
    return 'redirect:/auth/manage/comments.html'


# 后台管理评论列表
@get('/auth/manage/comments.html')
def manage_comments(*, page='1'):
    page_index = get_page_index(page)
    num = yield from Comment.findNumber('count(id)')
    p = Page(num, page_index=page_index, page_url='/auth/manage/comments.html?page=')
    comments = ()
    if num == 0:
        pass
        # return dict(page=p, comments=())
    else:
        comments = yield from Comment.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return {
        '__template__': 'b_manage_comments.html',
        'comments': comments,
        'page': p
    }


# 后台管理日志列表
@get('/auth/manage/blogs.html')
def manage_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = yield from Blog.findNumber('count(id)')
    p = Page(num, page_index=page_index, page_url='/auth/manage/blogs.html?page=')
    blogs = ()
    if num == 0:
        pass
    else:
        blogs = yield from Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return {
        '__template__': 'b_manage_blogs.html',
        'blogs': blogs,
        'page': p
    }


# 新建日志，直接跳转页面就是
@get('/auth/manage/blog/create.html')
def manage_create_blog():
    return {
        '__template__': 'b_manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }


# 编辑日志界面跳转
@get('/manage/blogs/edit')
def manage_edit_blog(*, id):
    return {
        '__template__': 'b_manage_blog_edit.html',
        'id': id,
        'action': '/api/blogs'
    }


# 后台管理用户列表
@get('/auth/manage/users.html')
def manage_users(*, page='1'):
    page_index = get_page_index(page)
    num = yield from User.findNumber('count(id)')
    p = Page(num, page_index=page_index, page_url='/auth/manage/users.html?page=')
    users = ()
    if num == 0:
        pass
    else:
        users = yield from User.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    for u in users:
        u.passwd = '******'
    # return dict(page=p, users=users)
    return {
        '__template__': 'b_manage_users.html',
        'users': users,
        'page': p
    }


# 后台管理mzt
@get('/auth/manage/mzt.html')
def manage_mzt(*, page='1'):
    page_index = get_page_index(page)
    p = Page(10, page_index=page_index, page_url='/auth/manage/mzt.html?page=')
    return {
        '__template__': 'b_manage_mzitu.html',
        'page': p
    }


# 后台管理mHauTai
@get('/auth/manage/mht.html')
def manage_mht(*, page='1'):
    page_index = get_page_index(page)
    num = yield from CIndexAll.findNumber('count(id)')
    p = Page(num, page_index=page_index, page_size=5, page_url='/auth/manage/mht.html?page=')
    index_all_by_page = yield from CIndexAll.findAll(orderBy='id desc', limit=(p.offset, p.limit))
    return {
        '__template__': 'b_manage_mht.html',
        'page': p,
        'index': index_all_by_page
    }


@get('/api/comments')
def api_comments(*, page='1'):
    page_index = get_page_index(page)
    num = yield from Comment.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = yield from Comment.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)


# 日志评论保存
@post('/api/blogs/{id}/comments')
def api_create_comment(id, request, *, content):
    user = request.__user__
    if user is None:
        raise APIPermissionError('Please signin first.')
    if not content or not content.strip():
        raise APIValueError('content')
    blog = yield from Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    comment = Comment(blog_id=blog.id, user_id=user.id, user_name=user.name, user_image=user.image,
                      content=content.strip())
    yield from comment.save()
    return comment


# 管理员 权限角色 删除评论-->成功返回{id:'delete_id'}
@post('/api/comments/{id}/delete')
def api_delete_comments(id, request):
    check_admin(request)
    c = yield from Comment.find(id)
    if c is None:
        raise APIResourceNotFoundError('Comment')
    yield from c.remove()
    return dict(id=id)


@get('/api/users')
def api_get_users(*, page='1'):
    page_index = get_page_index(page)
    num = yield from User.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = yield from User.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    for u in users:
        u.passwd = '******'
    return dict(page=p, users=users)


_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


@post('/api/users')
def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name', message='用户名必须填写!!!')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email', message='邮箱格式不正确!!!')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd', message='密文密码格式不正确!!!')
    users = yield from User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', '此邮箱不可用，请更换邮箱地址!!!')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
                image='/static/ui/img/head/ih_' + str(random.randint(0, 13)) + '.png')
    yield from user.save()
    # make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/api/blogs')
def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = yield from Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = yield from Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)


# 获取日志 单条
@get('/api/blogs/{id}')
def api_get_blog(*, id):
    blog = yield from Blog.find(id)
    return blog


# 保存日志
@post('/api/blogs')
def api_create_blog(request, *, name, summary, content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image,
                name=name.strip(), summary=summary.strip(), content=content.strip())
    yield from blog.save()
    return blog


@post('/api/blogs/{id}')
def api_update_blog(id, request, *, name, summary, content):
    check_admin(request)
    blog = yield from Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    yield from blog.update()
    return blog


@post('/api/blogs/{id}/delete')
def api_delete_blog(request, *, id):
    check_admin(request)
    blog = yield from Blog.find(id)
    yield from blog.remove()
    return dict(id=id)


# mZiTu start
@get('/mZiTu.html')
def index_mzt(*, page='1'):
    # page_index = get_page_index(page)
    # num = yield from Blog.findNumber('count(id)')
    # page = Page(num)
    # if num == 0:
    #     blogs = []
    # else:
    #     blogs = yield from Blog.findAll(orderBy='created_at desc', limit=(page.offset, page.limit))
    return {
        '__template__': 'h_mzitu.html'
        # 'page': [1],
        # 'blogs': blogs
    }


# mZiTu end


# index start
@get('/index.html')
def index_home():
    pass
    return {
        '__template__': 'h_index.html'
    }


# index end


# manHuaTai start
# 漫画台首页
@get('/manHuaTai.html')
def mht_home(*, page='1'):
    page_index = get_page_index(page)
    num = yield from CIndexAll.findNumberByJoin('count(m.id)',
                                                join_tb=' m left join mht_comic_info mi on m.id = mi.index_id ',
                                                where='mi.share_times is not null')
    page = Page(num, page_index=page_index, page_size=12, page_url='/manHuaTai.html?page=')

    comic_index_page = yield from CIndexAll.findAllByJoin(
        fields='m.id, m.name, m.type, m.status, m.plot, m.pic, m.commons, m.index_url',
        join_tb=' m left join mht_comic_info mi on m.id = mi.index_id ',
        where='mi.share_times is not null',
        orderBy='mi.share_times desc',
        limit=(page.offset, page.limit))

    return {
        '__template__': 'h_mht_index.html',
        'comic_index': comic_index_page,
        'page': page
    }


# 漫画信息章节查看页面
@get('/mht/comic/{id}/info.html')
def mht_comic_id_info(*, id):
    # page_index = get_page_index(page)
    comic_info = yield from CComicInfo.findAll(where='index_id=?', args=[id])
    if comic_info is None or len(comic_info) != 1:
        return {'__template__': '404.html'}
    # comic_section = yield from CComicPicture.findAll(where='comic_id=?', args=[comic_info[0].id],
    #                                                  orderBy='sort_order desc')
    # # 加载第一张图片 循环太多次数据库，不推荐
    # for cs in comic_section:
    #     section_pic = yield from CComicSectionPic.findAll(
    #         where='section_id=?',
    #         args=[cs.id],
    #         orderBy='sort_order asc',
    #         limit=1)
    #     if section_pic is not None and len(section_pic) == 1:
    #         cs.href = section_pic[0].pic_url
    #     else:
    #         cs.href = ''

    # 改良版
    comic_section = yield from CComicPicture.findAllByJoin(
        fields='cp.id,cp.sort_order,mcs.pic_url href,cp.title,cp.comic_id',
        join_tb=' cp left join mht_comic_section_pic mcs on cp.id = mcs.section_id',
        where='cp.comic_id=? and (mcs.sort_order=1 or mcs.sort_order is null)',
        args=[comic_info[0].id],
        orderBy='cp.sort_order desc'
    )
    # # 避免未获取漫画图片页面 无数据显示
    # if comic_section is None or len(comic_section) == 0:
    #     comic_section = yield from CComicPicture.findAllByJoin(
    #         fields='cp.id,cp.sort_order,mcs.pic_url href,cp.title,cp.comic_id',
    #         join_tb=' cp left join mht_comic_section_pic mcs on cp.id = mcs.section_id',
    #         where='cp.comic_id=? and mcs.sort_order is null',
    #         args=[comic_info[0].id],
    #         orderBy='cp.sort_order desc'
    #     )

    return {
        '__template__': 'h_mht_comic.html',
        'comic_info': comic_info[0],
        'comic_section': comic_section
    }


# 漫画章节查看页面
@get('/mht/comic/{id}/look.html')
def mht_comic_look(*, id):

    # 获取章节对象信息
    section_info = yield from CComicPicture.find(id)
    if section_info is None:
        return {'__template__': '404.html'}
    # 获取漫画信息
    comic_info = yield from CComicInfo.find(section_info.comic_id)
    if comic_info is None:
        return {'__template__': '404.html'}
    # 获取章节图片信息
    comic_pictures = yield from CComicSectionPic.findAll(
        where='section_id=?',
        args=[section_info.id],
        orderBy='sort_order asc')
    if comic_pictures is None or len(comic_pictures) == 0:
        return {'__template__': '404.html'}
    # 当前页数：
    page_no = section_info.sort_order  # 页号
    comic_id = section_info.comic_id  # 漫画id
    page = {
        # 'pre': None,
        # 'next': None
    }
    # 上一章
    pre_page = yield from CComicPicture.findAll(
        where='comic_id=? and sort_order=?',
        args=[comic_id, page_no - 1])
    if pre_page is not None and len(pre_page) != 0:
        page['pre'] = pre_page[0].id

    # 下一章
    next_page = yield from CComicPicture.findAll(
        where='comic_id=? and sort_order=?',
        args=[comic_id, page_no + 1])
    if next_page is not None and len(next_page) != 0:
        page['next'] = next_page[0].id

    return {
        '__template__': 'h_mht_look_pic.html',
        'comic_info': comic_info,
        'section_info': section_info,
        'comic_pictures': comic_pictures,
        'page': page
    }


# 漫画台后管 查询一个漫画
@get('/api/search/{name}/comic')
def mht_search_name(request, *, name=''):
    if name.strip() == '' or len(name.strip()) < 2:
        return {'status': 'fail', 'err': '查询条件不符合要求，请从新输入查询条件'}
    check = check_super_admin(request)
    if check:
        return check
    name = '%' + name + '%'
    list_comic = yield from CIndexAll.findAll(where='name like ?', args=[name])
    if list_comic is None or len(list_comic) == 0:
        return {'status': 'fail', 'err': '查无记录，请联系超级管理员！'}
    return {'status': 'ok', 'msg': '执行成功！', 'list': list_comic}


#  漫画台索引页抓取，可以全量抓取，数据量大约 2万左右
@post('/api/mhtIndex')
def mht_index(request, *, main_url='http://www.manhuatai.com/all.html', thread_count=10, trans_id=next_id()):
    # main_url = 'http://www.manhuatai.com/all.html'
    check = check_super_admin(request)
    if check:
        return check

    num = yield from CIndexAll.findNumber('count(id)')
    if num > 0:
        return {'status': 'fail', 'err': '已经全量更新获取了此部分数据，请采用更新操作!'}

    thread_count = int(thread_count)
    if thread_count > 20:
        thread_count = 20
    mc = MHuaTai()
    # 共计523条
    all_index_url = mc.index_url(main_url)
    len_index = len(all_index_url)
    #
    size = len_index // thread_count
    if len_index > 0:
        parts = len_index // size
        is_int = len_index % size

        # 线程监控
        monitor_thread = []
        if is_int != 0:
            parts = parts + 1
        for i in range(0, parts):
            args = {}
            start = i * size
            end = (i + 1) * size
            if start > len_index:
                break
            args['list_url'] = all_index_url[start:end]
            args['method'] = 'index'
            mt = threading.Thread(target=process_thread_mht, args=(args,), name='漫画台索引页' + str(i + 1) + '部分')
            monitor_thread.append(mt)
    # 启动日志监控
    monitor_args = {
        'monitor_thread': monitor_thread,
        'message_type': '漫画台加载全部漫画索引',
        'trans_id': trans_id,
        'content': "初始化数据服务：总共：%s部分内容" % parts,
        'message_order': 1,
        'status': '预备等待执行...'
    }
    monitor = threading.Thread(target=process_thread_monitor, args=(monitor_args,), name='线程监控服务')
    monitor.start()
    dict_obj = {'status': 'ok', 'msg': '你的操作已经已经提交，奴家正在拼命...'}
    return dict_obj


# 执行流程日志记录
@get('/api/{trans_id}/logger')
def logger_message(*, start_order=0, trans_id):
    messages = yield from ProcessMessage.findAll(
        'trans_id=? and message_order>?',
        [trans_id, start_order],
        orderBy='message_order asc')
    if messages is None:
        return {'status': 'ok', 'obj': []}
    return {'status': 'ok', 'obj': messages}


@post('/api/{index_id}/comic_info')
def mht_comic_info(request, *, index_id=None, trans_id=next_id(), domain='http://www.manhuatai.com'):
    if index_id is None:
        return {'status': 'fail', 'err': '非正常处理流程!!!'}

    check = check_super_admin(request)
    if check:
        return check

    comic_info = yield from CComicInfo.findAll(where='index_id=?', args=[index_id])
    if len(comic_info) != 0:
        return {'status': 'fail', 'err': '【%s】此部分内容已经全量操作，请使用更新选择。' % comic_info[0].name}
    # 暂时处理一条吧
    comic_index = yield from CIndexAll.find(index_id)
    if comic_index is None:
        return {'status': 'fail', 'err': '无此记录！请联系DBA管理员!!!'}
    comic_index_id = comic_index.id
    url = domain + comic_index.index_url
    args = {
        'list_url': [url],
        'method': 'comic_info',
        'index_id': comic_index_id
    }
    monitor_thread = []
    mt = threading.Thread(target=process_thread_mht, args=(args,), name='漫画台详情页')

    # 线程监控
    monitor_thread.append(mt)
    # 启动日志监控
    monitor_args = {
        'monitor_thread': monitor_thread,
        'message_type': comic_index.name,
        'trans_id': trans_id,
        'content': "初始化数据服务：解析【%s】详情内容" % comic_index.name,
        'message_order': 1,
        'status': '预备等待执行...'
    }
    monitor = threading.Thread(target=process_thread_monitor, args=(monitor_args,), name='线程监控服务')
    monitor.start()

    return {'status': 'ok', 'msg': '操作流程已经提交至后台，请等待片刻查看结果!'}


@post('/api/{index_id}/comic_pic')
def comic_pic(request, *, index_id=None, trans_id=next_id(), comic_name='漫画章节图片信息'):
    if index_id is None:
        return {'status': 'fail', 'err': '非正常处理流程!!!'}

    check = check_super_admin(request)
    if check:
        return check
    # 检查是否已经全量更新过
    num = yield from CComicSectionPic.findNumberByJoin(
        'count(ms.id)',
        join_tb=''' ms 
            left join mht_comic_pic mp on ms.section_id = mp.id
            left join mht_comic_info mc on mp.comic_id=mc.id 
            left join mht_index_all m on mc.index_id=m.id''',
        where='m.id=?',
        args=(index_id,))
    if num is not None and num > 0:
        return {'status': 'fail', 'err': '【%s】此漫画章节图片已经全量操作，请使用更新选择。' % comic_name}
    # 传入的是 索引页的id,需要去查询 详情页id,
    comic_pic_list = yield from CComicPicture.findAllByJoin(
        fields='cp.id,cp.sort_order,cp.href,cp.title,cp.comic_id',
        join_tb=' cp left join mht_comic_info mc on cp.comic_id=mc.id left join mht_index_all m on mc.index_id=m.id',
        where='m.id=?',
        args=[index_id],
        orderBy='cp.sort_order asc')
    if comic_pic_list is None or len(comic_pic_list) <= 0:
        return {'status': 'fail', 'err': '请按照流程操作，先获取漫画详情！！！'}
    list_size = len(comic_pic_list)
    # 看看分为多少线程 并行
    if list_size % 10 == 0:
        count = list_size // 10
    else:
        count = list_size // 10 + 1
    if count > 20:
        count = 20
    # 线程分组：
    part = list_size // 10
    if part == 0:
        t_size = list_size
    else:
        t_size = list_size // part
    if count >= 20:
        t_size = list_size // 19
    # 线程监控
    monitor_thread = []
    for i in range(0, count):
        args = {}
        start = i * t_size
        end = (i + 1) * t_size
        if start > list_size:
            break
        args['comic_section_info'] = comic_pic_list[start:end]
        args['method'] = 'picture'
        mt = threading.Thread(target=process_thread_mht, args=(args,), name='漫画台漫画章节图片' + str(i + 1) + '部分')
        monitor_thread.append(mt)

    # 启动日志监控
    monitor_args = {
        'monitor_thread': monitor_thread,
        'message_type': comic_name,
        'trans_id': trans_id,
        'content': "初始化数据服务：解析【%s】漫画所有章节图片" % comic_name,
        'message_order': 1,
        'status': '预备等待执行...'
    }
    monitor = threading.Thread(target=process_thread_monitor, args=(monitor_args,), name='线程监控服务')
    monitor.start()

    return {'status': 'ok', 'msg': '操作流程已经提交至后台，请等待片刻查看结果!'}


# 更新指定章节的漫画信息
@post('/api/up/{section_id}/comic_pic')
def comic_pic_up(request, *, section_id=None, trans_id=next_id(), comic_name='漫画章节图片信息更新'):
    if section_id is None:
        return {'status': 'fail', 'err': '非正常处理流程!!!'}

    check = check_super_admin(request)
    if check:
        return check
    section_info = yield from CComicPicture.find(section_id)
    if section_info is None:
        return {'status': 'fail', 'err': '未有次章节信息【%s】!!!,请联系超级管理员核实。' % section_id}

    # 线程监控
    monitor_thread = []
    args = {
        'comic_section_info': section_info,
        'method': 'up_picture'
    }
    mt = threading.Thread(target=process_thread_mht, args=(args,), name='漫画台漫画章节图片修复' + section_info.title + '部分')
    monitor_thread.append(mt)
    # 启动日志监控
    monitor_args = {
        'monitor_thread': monitor_thread,
        'message_type': comic_name + '【' + section_info.title + '】',
        'trans_id': trans_id,
        'content': "初始化数据服务：修复【%s】漫画章节图片" % section_info.title,
        'message_order': 1,
        'status': '预备等待执行...'
    }
    monitor = threading.Thread(target=process_thread_monitor, args=(monitor_args,), name='线程监控服务')
    monitor.start()
    return {'status': 'ok', 'msg': '操作流程已经提交至后台，请等待片刻查看结果!'}


@get('/api/{comic_id}/comic_pic')
def get_comic_pic_info(comic_id):

    if comic_id is None:
        return {'status': 'fail', 'err': '非正常处理流程!!!'}
    comic_index = yield from CComicInfo.findAll(where='index_id=?', args=[comic_id])
    if comic_index is None or len(comic_index) == 0:
        return {'status': 'fail', 'err': '请先执行获取漫画详情操作!!!'}
    all_pic = yield from CComicPicture.findAll(
        where='comic_id=?',
        args=[comic_index[0].id],
        orderBy='sort_order desc')
    if all_pic is None or len(all_pic) == 0:
        return {'status': 'fail', 'err': '请先选着获取章节漫画图片信息，再使用修复功能!!!'}
    return {'status': 'ok', 'data': all_pic}


# manHuaTai end


# about me start
@get('/me.html')
def me_home():
    pass
    return {
        '__template__': 'h_index.html'
    }


# about me end


@get('/404.html')
def not_found_page():
    return {
        '__template__': '404.html'
    }
