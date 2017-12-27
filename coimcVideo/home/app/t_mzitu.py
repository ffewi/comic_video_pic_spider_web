import threading
from home.app.models import *


# 创建全局ThreadLocal对象:
local_var = threading.local()


def process_mzt():
    # 获取当前线程关联的student:
    args = local_var.args
    print('Hello, %s (in %s)' % (args, threading.current_thread().name))
    print(args['name'])


def process_thread_mzt(args):
    # 绑定ThreadLocal的student:
    local_var.args = args
    process_mzt()


# t1 = threading.Thread(target=process_thread_mzt, args=({'name':'hello','age':23},), name='Thread-A')
# # t2 = threading.Thread(target=process_thread_mzt, args=('Bob',), name='Thread-B')
# t1.start()
# # t2.start()
# t1.join()
# # t2.join()
