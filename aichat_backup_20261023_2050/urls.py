# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = 'aichat'

urlpatterns = [
    path('', views.page, name='page'),

    path('api/bootstrap/', views.bootstrap, name='bootstrap'),
    path('api/models/', views.models, name='models'),

    path('api/conversations/', views.conversations, name='conversations'),
    path('api/conversations/<int:cid>/', views.conversation_detail, name='conversation'),
    path('api/conversations/<int:cid>/messages/', views.conversation_messages, name='messages'),
    path('api/conversations/<int:cid>/messages/<int:mid>/', views.message_detail, name='message'),

    path('api/chat/', views.chat, name='chat'),
    path('api/upload/', views.upload, name='upload'),
    path('api/files/', views.files, name='files'),
    path('api/files/<str:name>/', views.file_download, name='download'),
]
