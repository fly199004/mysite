from django.contrib import admin
from django.urls import path,include
from django.views.static import serve
from django.conf import settings
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('index/',views.index,name='index'),
    path('test/',views.test,name='test'),
    path('articles/',views.articles,name='articles'),
    path('articles/<str:article_id>/', views.articles, name='articles'),
    path('post/',views.post,name='post'),
    path('post/<int:article_id>/', views.post, name='post'),
    path('reading/', views.reading, name='reading'),
    path('reading/<int:article_id>/', views.reading, name='reading'),
    path('teach/', views.teach, name='teach'),
    path('teach/<int:article_id>/', views.teach, name='teach'),
    path('tech/', views.tech, name='tech'),
    path('tech/<int:article_id>/', views.tech, name='tech'),
    path('me/', views.me, name='me'),
    path('datav/', views.datav, name='datav'),
    path('aboutme/', views.me, name='me'),
    path('c/aboutme/', views.me, name='me'),
    path('dh/',views.dh,name='dh'),

    # ---------------- 静态专题页 ----------------
    # 高性价比人生指南（独立单文件静态页）
    path('life-guide/', serve, kwargs={'path': 'life-guide.html', 'document_root': settings.BASE_DIR / 'static'}, name='life_guide'),

    # ---------------- 在线工具 ----------------
    path('tools/knowmap/', views.tool_knowmap, name='tool_knowmap'),
    path('tools/label/', views.tool_label_generator, name='tool_label'),
    path('tools/prompter/', views.tool_prompter, name='tool_prompter'),
]
