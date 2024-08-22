from django.contrib import admin
from django.urls import path,include
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
]