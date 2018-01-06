import re
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import pymongo
from config import *


driver = webdriver.Chrome()
# 设置等待时间
wait = WebDriverWait(driver, 10)
# 定义MongoDB客户端,将MongoDB客户端与指定的url相连接，此处为本地服务器。
licent = pymongo.MongoClient(MONGO_URL)
# 定义MongoDB数据库。
db = licent[MONGO_DB]


# 定义一个搜索关键字的函数
# try...except语句用于抛出TimeoutException.
def search():
    try:
        driver.get('http://www.taobao.com')
        # 判断搜索框是否加载成功并定位到搜索框
        keys_input_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        # 判断元素是否是可点击的，若是则定位到这个按钮。
        submit_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))
        )
        # 在搜索框内发送美食关键字。
        keys_input_box.send_keys('美食')
        # 点击提交按钮。
        submit_button.click()
        # 获取页面的总页数，定位到总页数的元素部分
        total_pages = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total'))
        )
        parse_the_page()
        # text用于获取html标签内的内容。
        return total_pages.text
    except TimeoutException:
        return search()


# 定义一个翻页的函数
def turn_the_page(page_index):
    try:
        # 检查页码输入框是否加载成功，若成功就定位到这个页码输入框。
        page_input_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        # 检查元素是否加载成功，若成功检查元素是否可点击，若可点击，就定位到该元素。
        submit_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        # 清空页码输入框，若不清空的话，第一次输入2，第二次输入的就是23，第三次输入的就是234.
        page_input_box.clear()
        # 输入要跳转的页码
        page_input_box.send_keys(page_index)
        # 点击【确定】按钮
        submit_button.click()
        # 检查页面是否跳转成功。若不成功程序就会中断。
        # 使用text_to_be_present_in_element方法，它的作用是判断定位的元素的内容和后面的str参数是否相等。
        # 定位的这个元素是如果在第n页，则这个元素高亮显示n。
        # str(page_index)指的是输入的要跳转的页码。
        wait.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'),
                str(page_index))
        )
        parse_the_page()
        print('这是第', page_index, '页')
    except TimeoutException:
        return turn_the_page(page_index)


def main():
    total_pages = search()
    # 使用正则表达式提取内容【共 100 页】中的数字。
    total_pages = int(re.compile('(\d+)').search(total_pages).group(1))
    for i in range(2, total_pages+1):
        turn_the_page(i)


# 解析爬取页面
def parse_the_page():
    # 通过属性page_source获取网页的html代码，即点击【检查】看到的内容。
    html = driver.page_source
    # 使用pyquery解析数据
    # 首先以html为参数创建pyquery对象
    doc = pq(html)
    # 定位到要爬取的元素，看是否加载成功。如果失败的话程序会中断。
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item'))
    )
    # 使用pyquery获取要爬取的元素。首先缩小爬取范围。
    # 等会查看pyquery的API。
    data = doc('#mainsrp-itemlist .items .item').items()
    # 然后再小范围内爬取数据。
    for item in data:
        product = {
            'title': item.find('.title .J_ClickStat').text(),
            'price': item.find('.price').text(),
            'shop': item.find('.shop .shopname').text(),
            'pic': item.find('.pic .img').attr('src'),
            'deal': item.find('.deal-cnt').text()[:-3],
            'location': item.find('.location').text()
        }
        save_to_mongo(product)


# 参数为要传入数据库的数据。
def save_to_mongo(data):
    try:
        if db[MONGO_TABLE].insert(data):
            print('存储到数据库成功', data)
    except Exception:
        print('存储到数据库失败', data)


if __name__ == '__main__':
    main()
