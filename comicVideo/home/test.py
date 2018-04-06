# s1 = '''
# 分类：性感妹子
# 发布于 2017-12-27 22:20
# 5,153次浏览
# '''
# t = s1[0:s1.index('发布于')].replace('\n','')
# ti = s1[s1.index('发布于'):s1.index('\n',s1.index('发布于'))].replace('\n','')
# v = s1[(s1.index('\n',s1.index('发布于')+1)):len(s1)].replace('\n','')
# print(t,ti,v,sep='\n')
#
# ss = 'hello \n my odl body \n hahahah'
# print(ss.replace('\n1','',10))
# import base64
# import requests
# re=requests.get('http://i.meizitu.net/2017/12/27c23.jpg', headers={'User-Agent': "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
#                                                                    'Referer': 'http://www.mzitu.com/2017/12'})
# bstr = base64.b64encode(re.content)
# print(bstr)
# a = {'1':None,'2':'22'}
# print(tuple(a.values()))
import time
# da = {}
# da['ddd'] = {'data':{},'ttl':time.time()}
# da['ddd1'] = {'data':{},'ttl':time.time()+10}
# # del da['ddd']
# while len(da):
#     t = time.time()
#     kk = []
#     for i in da:
#         if t - da[i]['ttl'] > 2:
#             print('删除key：', i)
#             kk.append(i)
#         else:
#             time.sleep(1)
#             print(da[i])
#     for i in kk:
#         del da[i]
# print(da)
#
# a = {'ii':1}
# print('ii' in a)
# s = 123124324
# a = []
# while s != 0:
#     s3 = s % 1000
#     s = s // 1000
#     a.append(str(s3))
# a.reverse()
# print(','.join(a))
ss=time.strftime('%Y-%m-%d', time.localtime(time.time()))
print(ss)
