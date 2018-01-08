import time

from home.app.MySQL import Mysql
from home.app.models import next_id

__author__ = 'ffewi'
pool_mysql = Mysql()


def process_thread_monitor(args):
    all_sub_thread = args.get('monitor_thread', None)
    del args['monitor_thread']
    # 插入一条日志 启动功能日志
    sql = '''insert into process_message(content,message_type,trans_id,status,message_order,created_at,id) 
           values(%s,%s,%s,%s,%s,%s,%s)'''
    values = [args['content'], args['message_type'], args['trans_id'], args['status'], args['message_order'],
              time.time(), next_id()]
    pool_mysql.insertOne(sql, values)
    pool_mysql.end()
    for thread in all_sub_thread:
        thread.start()

    # 检查 是否执行完毕
    time.sleep(2)
    alive_count = run_complete(all_sub_thread)
    while alive_count > 0:
        values[-1] = next_id()
        values[4] = values[4] + 1
        values[3] = '执行中...'
        values[0] = values[1] + '--剩余%s 部分内容' % alive_count
        values[5] = time.time()
        pool_mysql.insertOne(sql, values)
        pool_mysql.end()
        time.sleep(5)
        alive_count = run_complete(all_sub_thread)
    # 执行完毕
    values[0] = values[1] + '所有部分内容执行完毕！'
    values[-1] = next_id()
    values[4] = values[4] + 1
    values[3] = '执行完毕!!!'
    values[5] = time.time()
    pool_mysql.insertOne(sql, values)
    pool_mysql.end()


def run_complete(threads):
    count = 0
    if threads is None:
        return count
    for thread in threads:
        if thread.isAlive():
            count = count + 1
    return count
