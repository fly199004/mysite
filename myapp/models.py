from djongo import models
from bson import ObjectId
import markdown,re

class Article(models.Model):
    _id = models.ObjectIdField()  # MongoDB中的ObjectId
    title = models.CharField(max_length=255)
    content = models.TextField()
    tags = models.JSONField()  # 假设tags是一个数组
    top = models.IntegerField(default=0)
    category = models.CharField(max_length=100)
    hidden = models.BooleanField(default=False)
    author = models.CharField(max_length=100)
    pathname = models.CharField(max_length=255, blank=True)
    private = models.BooleanField(default=False)
    password = models.CharField(max_length=255, blank=True)
    deleted = models.BooleanField(default=False)
    viewer = models.IntegerField(default=0)
    visited = models.IntegerField(default=0)
    createdAt = models.DateTimeField()
    updatedAt = models.DateTimeField()
    lastVisitedTime = models.DateTimeField()

    def __str__(self):
        return self.title

    def __init__(self):
        # 连接到 MongoDB
        self.client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
        self.db = self.client[settings.DATABASES['default']['NAME']]

    def get_articles(self, category=None):
        """获取文章列表，可根据分类进行过滤"""
        query = {}
        if category:
            query['category'] = category
        articles = self.db.articles.find(query, {"title": 1, "id": 1})
        return [{'id': article['id'], 'title': article['title']} for article in articles]

    def get_article_by_id(self, article_id, category=None):
        """根据数字 id 获取文章详情，可根据分类进行过滤"""
        query = {'id': int(article_id)}
        if category:
            query['category'] = category
        article = self.db.articles.find_one(query)
        return get_article_content(article) if article else None


# 解析文章内容中的图床 URL 并将它们转换为 <img> 标签
def process_image_urls(content):
    # 使用正则表达式找到所有图床URL并替换为 <img> 标签
    pattern = r'!\[(.*?)\]\((.*?)\)'  # 匹配 Markdown 格式的图片
    replacement = r'<img src="\2" alt="\1">'
    processed_content = re.sub(pattern, replacement, content)
    return processed_content

# 根据文章的 _id 或 id 字段获取文章的详细内容
def get_article_content(article):
    selected_article = {
        'title': article.get('title'),
        'author': article.get('author'),
        'createdAt': article.get('createdAt').strftime('%Y-%m-%d %H:%M:%S') if article.get('createdAt') else ''
    }
    
    # 获取文章内容并处理
    content = article.get('content', '')
    processed_content = process_image_urls(content)
    
    # 使用 toc 生成目录和 HTML 内容
    md = markdown.Markdown(extensions=['toc', 'extra'])
    html_content = md.convert(processed_content)
    toc_content = md.toc  # 获取目录内容
    
    selected_article['content'] = html_content
    selected_article['toc'] = toc_content
    
    return selected_article
   