# 关于MongoDB服务器的配置，包括URL,数据库名，表名。
# MongoDB服务器的url，这里指的是本地服务器
MONGO_URL = 'localhost'
# MongoDB数据库名
MONGO_DB = 'taobao'
# MongoDB表名
MONGO_TABLE = 'meishi'

"""
# mongoDB的连接方法
1.首先在配置文件中配置服务器信息
    MONGO_URL->url
    MONGO_DB-->数据库名
    MONGO_TABLE->数据表名
2.然后在程序中定义客户端配置
     2.1将mongo客户端与本地MongoDB服务器相连
        client = pymongo.MongoClient(MONGO_URL)
     2.2定义连接的数据库
        db = client[MONGO_DB]
     2.3将数据存入指定数据库的数据表中
        db[MONGO_TABLE].insert(<要传入的数据，字典形式>)
"""