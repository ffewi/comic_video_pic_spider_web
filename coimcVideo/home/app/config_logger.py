import logging

# 日子配置参数
kwargs = {
    'level': logging.INFO,
    'datefmt': '%Y/%m/%d %H:%M:%S',
    'format': '%(asctime)s %(name)s-%(levelname)s %(filename)s [line:%(lineno)d]  %(message)s',
    # 'filename': 'app.log', 输出文件
    # 'filemode': 'w' 输出模式
}

logging.basicConfig(**kwargs)

baseLog = logging
log = baseLog.getLogger('基本日志')
# log.info('你现在打印的是基本日志')
