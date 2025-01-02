from pymongo import MongoClient

# 替换为实际的远程 MongoDB 地址、用户名和密码
host = "mongodb://47.113.145.248:27017/vanBlog"

try:
    # 创建 MongoDB 客户端
    client = MongoClient(host)

    # 测试连接
    db = client['vanBlog']
    print("Connected to MongoDB!")
    
    # 查看集合列表
    print("Collections:", db.list_collection_names())
except Exception as e:
    print("Failed to connect to MongoDB:", e)
