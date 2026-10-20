"""AI 对话子页路由。"""
from django.urls import path

from . import views

app_name = 'aichat'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/models/', views.api_models, name='api_models'),
    path('api/chat/', views.api_chat, name='api_chat'),
    path('api/upload/', views.api_upload, name='api_upload'),
    path('api/files/', views.api_files, name='api_files'),
    path('api/files/<str:name>/', views.api_download, name='api_download'),
]
