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
# Create your views here.

def index(request):
    return render(request, 'index.html')

def test(request):
    return render(request, 'test.html')


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
                'content': article.get('content'),
                'author': article.get('author'),
                'createdAt': article.get('createdAt').strftime('%Y-%m-%d %H:%M:%S') if article.get('createdAt') else ''
            }

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