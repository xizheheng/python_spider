import re
import requests
from requests import RequestException
from maoyan_config import *
import pymongo
# 使用多进程运行程序，导入进程池包
from multiprocessing import Pool


client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


# 得到网页的html代码
def get_html(url):
    # try...except语句是为了抛出请求页面时所遇到的异常。
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None


def parse_the_html(html):
    # 定义一个提取数据的正则表达式
    pattern = re.compile('<dd>.*?board-index.*?>(.*?)</i>.*?data-src="(.*?)".*?title="(.*?)"'
                         + '.*?star">(.*?)</p>.*?releasetime">(.*?)</p>.*?integer">(.*?)</i>.*?fraction">(.*?)</i>', re.S)
    # results为一个list，里面的每个元素为一个元组。
    results = pattern.findall(html)
    # i 是一个元组。
    for i in results:
        # 使用yield把方法变成一个生成器。
        yield {
            '排名': i[0],
            '图片': i[1],
            '名称': i[2].strip(),
            '主演': i[3].strip()[3:],
            '上映时间': i[4][5:],
            '评分': i[5] + i[6]
        }


def main(offset):
    html = get_html('http://maoyan.com/board/4?offset=' + str(offset))
    results = parse_the_html(html)
    for i in results:
        print(i)
        save_to_mongo(i)


def save_to_mongo(data):
    try:
        if db[MONGO_TABLE].insert(data):
            print('存储到数据库成功',)
    except Exception:
        print('存储到数据库失败',)


if __name__ == '__main__':
    pool = Pool()
    # map()方法第一个参数为一个函数，第二个参数为一个列表。它的作用是将列表中的元素给第一个参数。
    pool.map(main, [i * 10 for i in range(10)])
    """# for i in range(0, 10):
           # main(i * 10)"""