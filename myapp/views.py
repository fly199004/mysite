from django.shortcuts import render
# urls.py
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from .models import *
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


def articles(request, article_id=None):
    # 连接到 MongoDB
    client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
    db = client[settings.DATABASES['default']['NAME']]   

    # 查询所有文章标题
    articles = db.articles.find({}, {"title": 1})
    article_list = []
    for article in articles:
        article_list.append({
            'id':str(article['_id']),
            'title': article['title']
        })

    # 如果传递了文章ID，则获取文章详情
    selected_article = None
    if article_id:
        article = db.articles.find_one({'_id': ObjectId(article_id)})
        if article:
            selected_article = get_article_content(article)
    context = {
        'articles': article_list,
        'selected_article': selected_article
    }
    return render(request, 'articles.html', context)

def post(request, article_id=None):
    # 连接到 MongoDB
    client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
    db = client[settings.DATABASES['default']['NAME']]
        
    # 查询 所有文章标题
    articles = db.articles.find({},  {"title": 1, "id": 1})
    article_list = []
    for article in articles:
        article_list.append({
            'id': int(article['id']),  # 使用数字 id
            'title': article['title']
        })

    # 如果传递了文章ID（数字 id），则获取文章详情
    selected_article = None
    if article_id:
        article = db.articles.find_one({'id': int(article_id)})
        if article:
            selected_article = get_article_content(article)
    
    context = {
        'articles': article_list,
        'selected_article': selected_article
    }
    
    return render(request, 'post.html', context)

    

def reading(request, article_id=None):
    # 连接到 MongoDB
    client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
    db = client[settings.DATABASES['default']['NAME']]   

    # 查询 category 为 "reading" 的所有文章标题
    articles = db.articles.find({"category": "reading"}, {"title": 1, "id": 1})
    article_list = []
    for article in articles:
        article_list.append({
            'id': article['id'],  # 使用数字 id
            'title': article['title']
        })

    # 如果传递了文章ID（数字 id），则获取文章详情
    selected_article = None
    if article_id:
        article = db.articles.find_one({'id': int(article_id), 'category': 'reading'})
        if article:
            selected_article = get_article_content(article)
    
    context = {
        'articles': article_list,
        'selected_article': selected_article
    }
    
    return render(request, 'reading.html', context)

def teach(request, article_id=None):
    # 连接到 MongoDB
    client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
    db = client[settings.DATABASES['default']['NAME']]   

    # 查询 category 为 "teach" 的所有文章标题
    articles = db.articles.find({"category": "teach"}, {"title": 1, "id": 1})
    article_list = []
    for article in articles:
        article_list.append({
            'id': article['id'],  # 使用数字 id
            'title': article['title']
        })

    # 如果传递了文章ID（数字 id），则获取文章详情
    selected_article = None
    if article_id:
        article = db.articles.find_one({'id': int(article_id), 'category': 'teach'})
        if article:
            selected_article = get_article_content(article)
    
    context = {
        'articles': article_list,
        'selected_article': selected_article
    }
    return render(request, 'teach.html', context)

def tech(request, article_id=None):
    # 连接到 MongoDB
    client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
    db = client[settings.DATABASES['default']['NAME']]   

    # 查询 category 为 "teach" 的所有文章标题
    articles = db.articles.find({"category": "tech"}, {"title": 1, "id": 1})
    article_list = []
    for article in articles:
        article_list.append({
            'id': article['id'],  # 使用数字 id
            'title': article['title']
        })

    # 如果传递了文章ID（数字 id），则获取文章详情
    selected_article = None
    if article_id:
        article = db.articles.find_one({'id': int(article_id), 'category': 'tech'})
        if article:
            selected_article = get_article_content(article)
    
    context = {
        'articles': article_list,
        'selected_article': selected_article
    }
    return render(request, 'tech.html', context)
