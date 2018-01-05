"""使用selenium模仿浏览器抓取淘宝美食。
    为什么要用selenium？
    因为原始的document是通过js和ajax加载数据的，分析Ajax请求贼他妈烦
    使用selenium可以抓到我们直接点击"审查元素"所看到的html代码。
    步骤：
        一.拿到网页源代码。
            1.使用selenium模仿浏览器，搜索关键词为“美食”的结果，然后就得到了网页的html代码
        二.分析代码，爬取相关信息。
        三.存到数据库中。
"""
import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from config import *
import pymongo


# 将mongo客户端与本地MongoDB服务器相连
client = pymongo.MongoClient(MONGO_URL)
# 定义连接的数据库
db = client[MONGO_DB]


driver = webdriver.Chrome()
# WebDriverWait设置网页加载等待时间，如果规定时间内未加载成功则抛出异常。
wait = WebDriverWait(driver, 10)


# 设置phantonjs的窗口大小
# driver.set_window_size(1400, 900)


# 写一个搜索关键字的方法
def search():
    print('正在搜索...')
    # 如果网速过慢或浏览器加载异常，会产生TimeOutException，所以使用try语句包含。
    try:
        driver.get('https://www.taobao.com')
        # 判断网页是否加载成功
        # until是定位某一个元素(比如按钮，输入框)，它是设置某个条件来定位的。
        # presence_of_element_located()是否存在这个元素，如果存在locate(定位)到这个元素。
        search_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        # element_to_be_clickable()????????
        submit_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))
        )
        # 使用send_keys()方法发送关键字
        search_box.send_keys('美食')
        # click()代表点击这个按钮。
        submit_button.click()
        parse_the_page()
        # 查看总共的页数
        num_of_pages = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                  '#mainsrp-pager > div > div > div > div.total')))
        return num_of_pages.text
    except TimeoutException:
        return search()


# 实现页面翻页
def turn_the_page(page_num):
    print('正在翻页......', page_num)
    try:
        page_input_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input')))
        submit_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                                        '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        # 首先清楚输入框中的内容
        page_input_box.clear()
        # 然后输入页码，因为本来里面默认填2，再输入2的话就是22，再输入3的话就是223.
        page_input_box.send_keys(page_num)
        submit_button.click()
        # 判断是否翻页成功。
        # text_to_be_present_in_element()是判断某个元素是否存在指定的文本。By.CSS_SELECTOR代表某个元素，str(page_num)代表指定文本。
        # 调用函数时,参数超长时,多行显示,每行一个参数，首行不显示参数,余者按层次缩进显示。
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'),
            str(page_num)))
        parse_the_page()
    except TimeoutException:
        turn_the_page(page_num)


# 解析页面
def parse_the_page():
    # 先定位到指定的位置，同时也判断要爬取的html是否加载成功
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item'))
    )
    # 使用selenium中webdriver的page_source属性获取网页的html代码。
    html = driver.page_source
    # 使用pyquery解析html代码
    doc = pq(html)
    # items()得到所有选择的内容。
    data = doc('#mainsrp-itemlist .items .item').items()
    for item in data:
        produce = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price g_price g_price-highlight strong').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.baoyou-intitle icon-service-free').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        print(produce)
        save_to_mongo(produce)


# 这是一个错误示范，导致我的程序一直出错。因为最后的print语句写到了for循环的外面，导致输出不了。
# 以后要耐心检查，调试程序比写程序花的时间长。
"""def parse_the_page():
    # 先定位到指定的位置，同时也判断要爬取的html是否加载成功
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item'))
    )
    # 拿到网页的源代码
    html = driver.page_source
    doc = pq(html)
    # item()方法得到所提取的html的内容
    data = doc('#mainsrp-itemlist .items .item').items()
    for item in data:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price g_price g_price-highlight strong').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.baoyou-intitle icon-service-free').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
    print(product)"""


def main():
    # 返回页面总页数
    num_of_pages = search()
    # 使用正则表达式提取里面的数字
    num_of_pages = int(re.compile("(\d+)").search(num_of_pages).group(1))
    for i in range(2, num_of_pages + 1):
        print('这是第', i, '页')
        turn_the_page(i)
    driver.close()


# 参数data表示要传进去的数据,数据一般都是字典类型的。
def save_to_mongo(data):
    try:
        if db[MONGO_TABLE].insert(data):
            print('存储到MongoDB成功', data)
    except Exception:
        print('存储到MongoDB错误', data)


if __name__ == '__main__':
    main()
