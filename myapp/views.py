from django.shortcuts import render
# urls.py
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from .models import Article
from pymongo import MongoClient
from django.conf import settings
from django.http import JsonResponse
from pymongo import MongoClient
from django.conf import settings
from bson import ObjectId
import markdown,re
# Create your views here.

def index(request):
    return render(request, 'index.html')

def test(request):
    return render(request, 'test.html')

# 解析文章内容中的图床 URL 并将它们转换为 <img> 标签
def process_image_urls(content):
    # 使用正则表达式找到所有图床URL并替换为 <img> 标签
    pattern = r'!\[(.*?)\]\((.*?)\)'  # 匹配 Markdown 格式的图片
    replacement = r'<img src="\2" alt="\1">'
    processed_content = re.sub(pattern, replacement, content)
    return processed_content


def articles(request, article_id=None):
    # 连接到 MongoDB
    client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
    db = client[settings.DATABASES['default']['NAME']]
    
    # 查询所有文章标题
    articles = db.articles.find({}, {"title": 1})
    article_list = []
    for article in articles:
        article_list.append({
            'id': str(article['_id']),
            'title': article['title']
        })

    # 如果传递了文章ID，则获取文章详情
    selected_article = None
    if article_id:
        article = db.articles.find_one({'_id': ObjectId(article_id)})
        if article:
            selected_article = {
                'title': article.get('title'),                                                      
                'author': article.get('author'),
                'createdAt': article.get('createdAt').strftime('%Y-%m-%d %H:%M:%S') if article.get('createdAt') else ''
            }
            # 1. 获取文章内容
            content = article.get('content', '')
            # 2. 处理图床 URL
            processed_content = process_image_urls(content)
            # 3. 使用 toc 生成目录和 HTML 内容
            md = markdown.Markdown(extensions=['toc', 'extra'])
            html_content = md.convert(processed_content)
            toc_content = md.toc  # 获取目录内容
            # 将处理后的 HTML 内容赋值给 selected_article 的 'content' 字段
            selected_article['content'] = html_content
            # 将目录内容赋值给 selected_article 的 'toc' 字段
            selected_article['toc'] = toc_content
           
           

           

    context = {
        'articles': article_list,
        'selected_article': selected_article
    }
    return render(request, 'articles.html', context)

# def article_detail(request, article_id):
#     # 连接到 MongoDB
#     client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
#     db = client[settings.DATABASES['default']['NAME']]
    
#     # 查询指定的文章
#     article = db.articles.find_one({'_id': ObjectId(article_id)})
    
#     # 将文章数据转为 JSON 格式
#     if article:
#         article_data = {
#             'title': article.get('title'),
#             'content': article.get('content'),
#             'author': article.get('author'),
#             'createdAt': article.get('createdAt').strftime('%Y-%m-%d %H:%M:%S') if article.get('createdAt') else '',
#         }
#     else:
#         article_data = {}

#     return JsonResponse(article_data)