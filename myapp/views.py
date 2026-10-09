from django.shortcuts import render, redirect
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

def datav(request):
    return render(request, 'datav.html')

# ---------------- 在线工具 ----------------
def tool_knowmap(request):
    """通用知识图谱生成器（不限学科）。"""
    return render(request, 'tools/knowmap.html')

def tool_label_generator(request):
    """二维码标签生成器（免费5次，之后需登录）。"""
    return render(request, 'tools/label_generator.html')

def tool_prompter(request):
    """飞云轩提词器（免费5次，之后需登录）。"""
    return render(request, 'tools/prompter.html')

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
    if article_id:
        return redirect('notes:legacy', domain_id='reading',
                        legacy_id=article_id, permanent=True)
    return redirect('/notes/reading/', permanent=True)

def teach(request, article_id=None):
    if article_id:
        return redirect('notes:legacy', domain_id='teach',
                        legacy_id=article_id, permanent=True)
    return redirect('/notes/teach/', permanent=True)

def tech(request, article_id=None):
    if article_id:
        return redirect('notes:legacy', domain_id='tech',
                        legacy_id=article_id, permanent=True)
    return redirect('/notes/tech/', permanent=True)


def dh(request):
    return render(request, 'dh/dh.html')
