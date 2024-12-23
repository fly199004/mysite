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

def me(request):
    return render(request, 'me.html')

def article_view(request, category=None, article_id=None, template_name='articles.html'):
    manager = Article()
    
    # 获取文章列表（可选分类过滤）
    article_list = manager.get_articles(category=category)
    
    # 获取选中的文章详情
    selected_article = manager.get_article_by_id(article_id, category=category) if article_id else None
    
    context = {
        'articles': article_list,
        'selected_article': selected_article
    }
    
    return render(request, template_name, context)

def articles(request, article_id=None):
    return article_view(request, article_id=article_id, template_name='articles.html')

def post(request, article_id=None):
    return article_view(request, article_id=article_id, template_name='post.html')

def reading(request, article_id=None):
    return article_view(request, category="reading", article_id=article_id, template_name='reading.html')

def teach(request, article_id=None):
    return article_view(request, category="teach", article_id=article_id, template_name='teach.html')

def tech(request, article_id=None):
    return article_view(request, category="tech", article_id=article_id, template_name='tech.html')


def dh(request):
    return render(request, 'dh.html')
