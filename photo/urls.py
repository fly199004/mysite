from django.urls import path
from django.shortcuts import render
from . import *
from . import views

app_name = 'photo'

urlpatterns = [
    # path('', home, name='index'),    
    path('', views.photo_list, name='photo_list'),
    path('photo/<int:pk>/', views.photo_detail, name='photo_detail'),
    path('upload/', views.upload_photos, name='upload_photos'),
    path('test/', views.test, name='test'),
]