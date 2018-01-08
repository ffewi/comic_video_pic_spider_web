import threading

from home.app.MySQL import Mysql
from home.app.models import *
from home.app.models import next_id
from home.app.tool_mzitu_ import MZiTu

__author__ = 'ffewi'

# 创建全局ThreadLocal对象:
local_mzt_var = threading.local()


# 索引
def process_mzt_index_data():
    # 获取当前线程关联的args:
    args = local_mzt_var.args
    # 当前线程名称
    t_name = threading.current_thread().name
    base_url = args['base_url']
    logging.info(t_name + '开始妹子图索引 数据解析装入...')
    mzt = MZiTu()
    all_index = mzt.all_url(base_url)
    data = []
    for index in all_index:
        index['id'] = next_id()
        data.append(tuple(index.values()))
    pool_mysql = Mysql()
    pool_mysql.insertMany(
        'insert into ' + MIndex.__table__ + '(page_title,page_url,url_order,id) values(%s,%s,%s,%s)',
        data)
    pool_mysql.end()
    logging.info(t_name + '完成此部分：%s索引地址 数据初始化...' % '妹子图')


# 信息
def process_mzt_info_page():
    # 获取当前线程关联的args:
    args = local_mzt_var.args
    # 当前线程名称
    t_name = threading.current_thread().name
    mzt = MZiTu()
    group_url = args['index_url']
    logging.info(t_name + '开始妹子图套图组 数据解析装入...' + str(len(group_url)))
    pool_mysql = Mysql()
    for m_index in group_url:
        obj = mzt.get_url_info(m_index.page_url)  # 对象{} 格式
        all_pic = obj['img_list']
        # 单图信息
        pic_info_page = {
            'views': obj['views'],
            'pic_type': obj['pic_type'],
            'pic_title': m_index.page_title,
            'pic_url': all_pic[0]['img_url'],
            'created_at': obj['date'],
            'index_id': m_index.id,
            'id': next_id()
        }
        all_pic_data = []
        for pic in all_pic:
            pic_info = {
                'img_order': pic['order'],
                'img_url': pic['img_url'],
                'group_id': pic_info_page['id'],
                'id': next_id()
            }
            all_pic_data.append(tuple(pic_info.values()))
        pool_mysql.insertOne(
            'insert into ' + MPicture.__table__ +
            '(views,pic_type,pic_title,pic_url,created_at,index_id,id) values(%s,%s,%s,%s,%s,%s,%s)',
            tuple(pic_info_page.values()))

        pool_mysql.insertMany(
            'insert into ' + MPictureInfo.__table__ + '(img_order,img_url,group_id,id) values(%s,%s,%s,%s)',
            all_pic_data)
    pool_mysql.end()
    logging.info(t_name + '完成此部分：%s部分套图组 数据解析完毕...' % str(len(group_url)))


def process_thread_mzt(args):
    # 绑定ThreadLocal的args:
    local_mzt_var.args = args
    if args:
        if args.get('method', None) == 'index':
            process_mzt_index_data()
        elif args.get('method', None) == 'pic_group':
            process_mzt_info_page()
        elif args.get('method', None) is None:
            print('其他方法')

# t1 = threading.Thread(target=process_thread_mzt, args=({'name':'hello','age':23},), name='Thread-A')
# # t2 = threading.Thread(target=process_thread_mzt, args=('Bob',), name='Thread-B')
# t1.start()
# # t2.start()
# t1.join()
# # t2.join()
