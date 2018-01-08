# 获取数据工具
import requests
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from home.app.config_logger import baseLog

__author__ = 'ffewi'
logging = baseLog.getLogger('漫画台工具类')


class MHuaTai(object):
    __page_url__ = 'http://www.manhuatai.com/all_p%s.html'
    __times__ = 1
    __driver = None
    __pic_suf__ = '.jpg'
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
    # logging = None

    def __init__(self):
        self.headers = self.agents
        self.__driver = MHuaTai.init_driver()
        # self.logging = baseLog('漫画台工具类')

    @staticmethod
    def init_driver():
        # logging.info('初始化.. PhantomJs')
        if MHuaTai.__driver is None:
            desired_capabilities = DesiredCapabilities.PHANTOMJS.copy()
            # 从USER_AGENTS列表中随机选一个浏览器头，伪装浏览器
            desired_capabilities["phantomjs.page.settings.userAgent"] = MHuaTai.agents[random.randint(0, 16)]
            # 不载入图片，爬页面速度会快很多
            desired_capabilities["phantomjs.page.settings.loadImages"] = False
        __driver = webdriver.PhantomJS(
            executable_path=r'E:\Program Files\phantomjs-2.1.1-windows\bin\phantomjs.exe',
            desired_capabilities=desired_capabilities)
        return __driver

    # 测试 索引信息流程
    def main_start(self, url):
        all_index = self.index_url(url)
        i = 0
        ret_obj = {}
        for index in all_index:
            if i < self.__times__:
                i_url = all_index[index]
                # 获取 导航页漫画详情 list集合里面 json Object 信息{key:vlaue}
                data = self.comic_info(i_url)
                # 返回对象
                ret_obj[index] = data
            else:
                break
            i = i + 1
        return ret_obj

    # 所有漫画图地址 一个页面36个漫画 523个索引链接
    def index_url(self, url):

        # 调用request 函数把漫画地址传进去会返回给我们一个response
        html = self.request(url)
        # 先找总页数
        end_page = BeautifulSoup(html.text, 'lxml').find('div', class_='pages').findAll('a', class_='page')[
            -2].get_text()
        pages = list(range(1, int(end_page) + 1))
        # 存储漫画索引页 523页共计
        index_page = []
        for i in pages:
            comic_url = self.__page_url__ % i
            index_page.append(comic_url)
        # 返回漫画索引页 详情
        return index_page
        # all_div = BeautifulSoup(html.text, 'lxml').find_all('a', class_='sdiv')
        # all_a = BeautifulSoup(html.text, 'lxml').find('div', class_='all').find_all('a')

    # 索引页每个漫画信息
    def comic_info(self, url):
        # 一页 36个漫画
        html = self.request(url)
        # 所有漫画的div包裹区域 共计36个 == 一页整
        all_comic_div = BeautifulSoup(html.text, 'lxml').find_all('a', class_='sdiv')
        data = []
        for div in all_comic_div:
            list_div = div.contents
            # 图片地址 + 更新提示
            first_div = list_div[0].contents
            ab = first_div[0].text
            img = first_div[1]['data-url']
            # ul格式 显示的详细信息
            lis = list_div[1].contents[0].contents
            title = lis[0].text
            comic_type = lis[1].text
            if '类型' in comic_type:
                comic_type = comic_type.replace('类型', '')
            status = lis[2].text
            if '状态' in status:
                status = status.replace('状态', '')
            plot = lis[3].text
            if '剧情' in plot:
                plot = plot.replace('剧情', '')
            ob = {
                'name': title,
                'type': comic_type,
                'commons': ab,
                'pic': img,
                'status': status,
                'plot': plot,
                'index_url': div['href']
            }
            data.append(ob)
        return data

    # 传入漫画索引,获取当前页的漫画 == 漫画详情页信息
    def comic_page(self, url):
        # 漫画 信息 详情页 这个页面有 js 控制页面显示，需要用js插件
        html = self.request_with_js(url)
        # 信息
        comic_info = BeautifulSoup(html, 'lxml').find('div', class_='mainctx').find('div', class_='mhjsbody clearfix')
        # 图片信息
        pic_url = comic_info.contents[0].contents[0]['src']
        pic_title = comic_info.contents[0].contents[0]['title']
        # ul 信息
        ul = comic_info.contents[1].contents[0].contents
        name = ul[0].text
        status = ul[1].text
        author = ul[2].text
        comic_type = ul[3].text
        up_time = ul[4].text

        # 去除多以的抬头信息
        name = self.clear_msg(name, '名称：')
        status = self.clear_msg(status, '状态：')
        author = self.clear_msg(author, '作者：')
        comic_type = self.clear_msg(comic_type, '类型：')
        up_time = self.clear_msg(up_time, '更新：')

        # 分享次数
        share_times = comic_info.contents[1].contents[1].contents[1].contents[-1].text
        # 2017-12-24 发现分享有带万字
        if share_times is not None and '万' in share_times:
            share_times = str(float(share_times[0:-1]) * 10000)
        # 文章描述 -- 剧情
        plot = comic_info.contents[1].contents[1].contents[3].text

        # 章节
        comic_section = BeautifulSoup(html, 'lxml').find('div', class_='mainctx').find('div', id='alllist').find('div', class_='mhlistbody')
        mhlistbody = comic_section
        # 正式篇 暂时处理 正片
        topic1 = mhlistbody.contents[0]
        all_li = topic1.contents
        all_li_data = []  # 存储正式篇 序号集
        order = len(all_li)
        for li in all_li:
            # 链接地址，相对与url
            a_href = li.next['href']
            # 章节文字描述  第XXX话 神一样的对手 18P
            a_text = li.next.text
            ob = {
                'link_href': a_href,
                'text': a_text,
                'sort_order': order
            }
            all_li_data.append(ob)
            order = order - 1
        # 番外篇
        if len(mhlistbody.contents) == 2:
            # 存在番外篇
            msg = '提示：%s %s %s' % (name, '有番外篇，需要获取不？ 地址为：', url)
            logging.info(msg)
        re_obj = {
            'pic_url': pic_url,
            'pic_title': pic_title,
            'name': name,
            'status': status,
            'author': author,
            'type': comic_type,
            'up_time': up_time,
            'share_times': share_times,
            'plot': plot,
            'list': all_li_data
        }
        return re_obj

    # 获取漫画章节图片
    def comic_section_pic(self, url):
        comic_pic_html = self.request_with_js(url)
        div_src_pic = BeautifulSoup(comic_pic_html, 'lxml').find('div', id='comiclist').findAll('div', class_='mh_comicpic')
        if div_src_pic is None or len(div_src_pic) == 0:
            logging.info('url:%s ,未找到漫画图片内容' % url)
            return []
        # 此处获取 地址链接格式
        common_url = div_src_pic[0].contents[0]['src']
        pre_url = common_url[0:common_url.index(self.__pic_suf__)-1]
        suff_url = common_url[common_url.index(self.__pic_suf__)+4: len(common_url)]
        # 此处获取总共的页数 以用来拼接地址
        options = BeautifulSoup(comic_pic_html, 'lxml').find('div', class_='mh_headpager').find('select', class_='mh_select')
        size = options.contents[-1]['value']
        data_list = []
        for i in range(1, int(size)+1):
            data_list.append({
                'order': i,
                'pic_url': pre_url + str(i) + self.__pic_suf__ + suff_url
            })
        return data_list

    @staticmethod
    def clear_msg(content, pre):
        if pre in content:
            new_content = content.replace(pre, '')
            return new_content
        return content

    # 这个函数获取网页的response 然后返回
    def request(self, url):
        content = requests.get(url, headers={'User-Agent': self.agents[random.randint(0, 16)]})
        return content

    # 带js 脚本执行的页面
    def request_with_js(self, url):
        # service_args = ['--proxy=localhost:9999', '--proxy-type=socks5', ]
        driver = self.__driver
        driver.get(url)
        data = driver.page_source
        return data


# 测试
# mht = MHuaTai()
# mht.main_start('http://www.manhuatai.com/all.html')
# mht.comic_info('http://www.manhuatai.com/all_p1.html')
# page_info = mht.comic_page('http://www.manhuatai.com/douluodalu/')
# mht.request_with_js('http://www.manhuatai.com/douluodalu/')
# print(page_info)
# mht.comic_page('http://www.manhuatai.com/fengshendouzhanbang/')
# html = mht.request_with_js('http://www.manhuatai.com/fengshendouzhanbang/113.html')
# pics = mht.comic_section_pic('http://www.manhuatai.com/yaoshenjiquancai/196.html')
# print(pics)

