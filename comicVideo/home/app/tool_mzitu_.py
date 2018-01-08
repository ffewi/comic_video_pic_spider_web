# 获取数据工具
import requests
import time
import datetime
import random
import base64
from bs4 import BeautifulSoup
from home.app.config_logger import baseLog

logging = baseLog.getLogger('MZiTu工具')

__author__ = 'ffewi'


class MZiTu:

    agents = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
    ]

    def __init__(self):
        self.headers = self.agents

    # 获取所有地址链接
    def all_url(self, url):
        html = self.request(url)
        all_a = BeautifulSoup(html.text, 'lxml').find('div', class_='all').find_all('a')
        if all_a and all_a[0]:
            if '/old' in all_a[0]['href']:
                old_html = self.request(all_a[0]['href'])
                all_a_old = BeautifulSoup(old_html.text, 'lxml').find('div', class_='all').find_all('a')
                all_a = all_a[1:]

        link_list = []
        size = len(all_a) + len(all_a_old)
        for a in all_a_old:
            link_list.append({
                'text': a.text,
                'href': a['href'],
                'order': size
            })
            size = size - 1
        for a in all_a:
            link_list.append({
                'text': a.text,
                'href': a['href'],
                'order': size
            })
            size = size - 1

        return link_list

    # 获取单个url的详情 以及其子url-- 套图组
    def get_url_info(self, url):
        pic_first_page = self.request(url)
        description = BeautifulSoup(pic_first_page.text, 'lxml').find('div', class_='main-meta')
        # 基本信息
        pic_meta = self.deal_pic_info(description.text)
        # 页数
        pic_pagenavi = BeautifulSoup(pic_first_page.text, 'lxml').find('div', class_='pagenavi').find_all('span')[-2].text

        # 图片地址
        pic_img = BeautifulSoup(pic_first_page.text, 'lxml').find('div', class_='main-image').find('img')['src']

        # 拼接 图片地址组
        # 当前只看到这种类型
        pre_url = ''
        end_url = ''
        if '.jpg' in pic_img:
            lc_jpg = pic_img.index('.jpg')
            pre_url = pic_img[0:lc_jpg-2]
            end_url = pic_img[lc_jpg:]
        elif '.jpeg' in pic_img:
            lc_jpg = pic_img.index('.jpeg')
            pre_url = pic_img[0:lc_jpg - 2]
            end_url = pic_img[lc_jpg:]
        # 扩展
        else:
            logging.warning('******未处理图片类型：%s' % pic_img)
        all_img = []
        for i in range(1, int(pic_pagenavi) + 1):
            if i < 10:
                val = '0' + str(i)
            else:
                val = str(i)
            all_img.append({
                'order': i,
                'img_url': pre_url + val + end_url
            })

        # 以第一页浏览量统计
        pic_meta['views'] = int(pic_meta['views']) * int(pic_pagenavi)
        pic_meta['img_list'] = all_img
        return pic_meta

    def deal_pic_info(self, span):
        if span is None or len(span) == 0:
            return {
                'pic_type': '未分类',
                'date': time.time(),
                'views': '0'
            }
        if '发布于' in span:
            lc_publish = span.index('发布于')
            one_line = span[0:lc_publish].replace('\n', '', 2)
            tow_line = span[lc_publish:span.index('\n', lc_publish)].replace('\n', '', 2)
            three_line = span[span.index('\n', lc_publish):len(span)].replace('\n', '', 2)
            if '分类：' in one_line:
                one_line = one_line.replace('分类：', '')
            if '发布于 ' in tow_line:
                tow_line = tow_line.replace('发布于 ', '')
            if '次浏览' in three_line:
                three_line = three_line.replace('次浏览', '')
                if ',' in three_line:
                    three_line = three_line.replace(',', '', 2)
            return {
                'pic_type': one_line,
                'date': self.str2time(tow_line, '%Y-%m-%d %H:%M'),
                'views': three_line
            }

        else:
            return {
                'pic_type': '未分类',
                'date': time.time(),
                'views': '0'
            }

    @staticmethod
    def str2time(str_time, format_str='%Y-%m-%d'):
        if str_time is None or str_time.strip() == '':
            return time.time()
        t = time.strptime(str_time, format_str)
        y, m, d, h, mm, s = t[0:6]
        times = datetime.datetime(y, m, d, h, mm, s).timestamp()
        return times

    # 这个函数获取网页的response 然后返回
    def request(self, url):
        content = requests.get(url, headers={'User-Agent': self.agents[random.randint(0, 16)]})
        return content

    # 带referrer的请求 用以请求图片 返回base64编码，解决mzitu 防盗
    def request_referrer(self, url, referrer):
        head = {'User-Agent': self.agents[random.randint(0, 16)],
                'Referer': referrer}
        content = requests.get(url, headers=head)
        if content and content.content:
            base_data = base64.b64encode(content.content)
            return base_data
        else:
            return None


# 测试
# m = MZiTu()
# arr1 = m.all_url('http://www.mzitu.com/all')
# print(arr1)
# arr2 = m.get_url_info('http://www.mzitu.com/113834')
# print(arr2)
# content = m.request_referrer('http://i.meizitu.net/2017/01/20a32.jpg', 'http://www.mzitu.com/2017/12')
# print(str(content))
