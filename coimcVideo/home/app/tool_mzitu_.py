# 获取数据工具
import requests
from bs4 import BeautifulSoup


class MZiTu:

    def __init__(self):
        self.headers = {'User-Agent': "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"}

    # 所有图 套图系列
    def all_url(self, url):
        # 调用request函数把套图地址传进去会返回给我们一个response
        html = self.request(url)
        all_a = BeautifulSoup(html.text, 'lxml').find('div', class_='all').find_all('a')
        # 调试控制条数
        i = 1
        arr = list([])
        arr.append({'n': '测i是'})
        for a in all_a:
            if i > 2:
                break
            # print(a)
            data = {
                'url': a['href'],
                'text': a.text
            }
            arr.append(data)
            i = i + 1
        return arr


    # 这个函数获取网页的response 然后返回
    def request(self, url):
        content = requests.get(url, headers=self.headers)
        return content


# 测试
m = MZiTu()
arr1 = m.all_url('http://www.mzitu.com/all')
print(arr1)
