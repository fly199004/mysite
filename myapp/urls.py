from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('index/',views.index,name='index'),
    path('test/',views.test,name='test'),
    path('articles/',views.articles,name='articles'),
    path('articles/<str:article_id>/', views.articles, name='articles_detail'),
]