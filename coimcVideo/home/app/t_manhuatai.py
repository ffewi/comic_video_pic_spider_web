import threading

from home.app.MySQL import Mysql
from home.app.models import *
from home.app.tool_manhuatai import MHuaTai

logging = baseLog.getLogger('漫画台--多线程')

# 创建全局ThreadLocal对象:
local_mht_var = threading.local()


# 漫画台索引 数据
def process_mht_index_data():
    # 获取当前线程关联的args:
    args = local_mht_var.args
    # print(args)
    t_name = threading.current_thread().name
    # 分隔的索引URL
    list_url = args['list_url']
    mc = MHuaTai()
    # 每页 36条数据
    logging.info(t_name + '开始索引页 数据解析装入...' + str(len(list_url)))
    # times = 1
    # 测试
    # time.sleep(15)
    # logging.info(t_name + '完成此部分索引页 数据初始化...' + str(len(list_url)))
    # return 'ok'

    for i in list_url:
        # if times != 1:
        #     break
        url_name = i
        # list[dict]
        list_comic = mc.comic_info(url_name)
        # columns = 'name,type,status,plot,pic,commons,index_url,id'
        if len(list_comic):
            columns = ','.join(tuple(list_comic[0])) + ',id'
        else:
            continue  # 此次数据格式不符合要求，继续下一次
        data = []
        for comic in list_comic:
            comic['id'] = next_id()
            data.append(tuple(comic.values()))
            # 需要替换成同步方法，异步可不用， ===多线程。。。__getConn()
        pool_mysql = Mysql()
        pool_mysql.insertMany(
            'insert into ' + CIndexAll.__table__ + '(%s)' % columns + ' values(%s,%s,%s,%s,%s,%s,%s,%s) ',
            data)
        pool_mysql.end()
        # times = times + 1

    logging.info(t_name + '完成此部分索引页 数据初始化...' + str(len(list_url)))


# 漫画详情页
def process_mht_comic_page():
    # 获取当前线程关联的args:
    args = local_mht_var.args
    # print(args)
    t_name = threading.current_thread().name

    list_url = args['list_url']
    index_id = args['index_id']  # 对应索引页的id
    # 工具类 解析页面
    mc = MHuaTai()
    logging.info(t_name + '开始详情页 数据解析装入...' + str(len(list_url)))
    # 漫画详情页 地址集合 各种处理
    for i in list_url:
        url_name = i
        obj_data = mc.comic_page(url_name)  # {key:value, list:[]}
        list_data = obj_data.get('list', [])
        del obj_data['list']
        if len(obj_data):
            columns = ','.join(tuple(obj_data)) + ',index_id,id'
        else:
            continue  # 此次数据格式不符合要求，继续下一次
        pool_mysql = Mysql()
        # 漫画详情页
        obj_data['up_time'] = str2time(obj_data['up_time'])
        obj_data['index_id'] = index_id
        obj_data['id'] = next_id()
        pool_mysql.insertOne(
            'insert into ' + CComicInfo.__table__ + '(%s)' % columns + ' values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ',
            tuple(obj_data.values()))

        # 存放章节信息
        insert_list = []
        for m in list_data:
            ob = m  # 这个是个 {}
            ob['link_href'] = url_name + ob['link_href']
            ob['id'] = next_id()
            ob['comic_id'] = obj_data['id']
            insert_list.append(tuple(ob.values()))
        pool_mysql.insertMany(
            'insert into ' + CComicPicture.__table__ + '(href,title,sort_order,id,comic_id) values(%s,%s,%s,%s,%s)',
            insert_list)

    pool_mysql.end()
    logging.info(t_name + '完成此部分详情页 数据初始化...' + str(len(list_url)))


def process_mht_picture_data():
    # 获取当前线程关联的args:
    args = local_mht_var.args
    t_name = threading.current_thread().name

    comic_section_info = args['comic_section_info']  # 章节对象 id 也在这个对象里面
    # 工具类 解析页面
    mc = MHuaTai()
    logging.info(t_name + '开始章节图片 数据解析装入...【共计：%s】' % str(len(comic_section_info)))
    pool_mysql = Mysql()
    for info in comic_section_info:
        section_url = info['href']
        section_id = info['id']
        list_data = mc.comic_section_pic(section_url)
        # print(section_url)
        if list_data is None or len(list_data) == 0:
            continue

        # 准备这个章节的插入数据 填充 id  和 章节id
        insert_data = []
        for p in list_data:
            ob = p  # {}
            ob['section_id'] = section_id
            ob['id'] = next_id()
            insert_data.append(tuple(ob.values()))

        pool_mysql.insertMany(
            'insert into ' + CComicSectionPic.__table__ + '(sort_order,pic_url,section_id,id) values(%s,%s,%s,%s)',
            insert_data)
    pool_mysql.end()
    logging.info(t_name + '完成共计：%s章节图片 数据初始化...' % str(len(comic_section_info)))


# 修复 漫画浏览页面 图片问题
def process_mht_picture_up_section():
    args = local_mht_var.args
    t_name = threading.current_thread().name

    comic_section_info = args['comic_section_info']  # 章节对象{} id 也在这个对象里面

    mc = MHuaTai()
    logging.info(t_name + '开始章节图片修复 数据解析装入...【%s】' % comic_section_info.title)
    list_data = mc.comic_section_pic(comic_section_info.href)
    if list_data is None or len(list_data) == 0:
        logging.warning('url:【%s】请求数据无返回')
        return
    pool_mysql = Mysql()
    for ob in list_data:

        count = pool_mysql.update(
                    'update ' + CComicSectionPic.__table__ + ' set pic_url=%s where section_id=%s and sort_order=%s',
                    (ob['pic_url'], comic_section_info.id, ob['order']))
        if count is None or count != 1:
            logging.warning(
                '数据操作影响行异常【%s】,args[%s,%s,%s]' % (count, ob['pic_url'], comic_section_info.id, ob['order']))
    pool_mysql.end()
    logging.info(t_name + '完成修复：%s章节图片 数据...' % comic_section_info.title)


def process_thread_mht(args):
    # 绑定ThreadLocal的args:
    local_mht_var.args = args
    if args:
        if args.get('method', None) == 'index':
            process_mht_index_data()
        elif args.get('method', None) == 'comic_info':
            process_mht_comic_page()
        elif args.get('method', None) == 'picture':
            process_mht_picture_data()
        elif args.get('method', None) == 'up_picture':
            process_mht_picture_up_section()
        elif args.get('method', None) is None:
            print('其他方法')
