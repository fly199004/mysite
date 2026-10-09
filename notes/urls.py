from django.urls import path, re_path

from . import views

app_name = 'notes'

# 固定领域白名单，避免与文章 slug 抢占
_DOMAINS = 'reading|tech|teach|ai-news'

urlpatterns = [
    path('', views.index, name='index'),

    # 三大栏目
    path('xuan/', views.section_xuan, name='section_xuan'),
    path('it/', views.section_it, name='section_it'),
    path('teach/', views.section_teach, name='section_teach'),

    path('books/', views.books, name='books'),
    path('books/<str:book_id>/', views.book_detail, name='book_detail'),
    path('asset/<path:path>', views.asset, name='asset'),

    # 旧数字 id 永久跳转
    path('legacy/<str:domain_id>/<int:legacy_id>/',
         views.legacy_redirect, name='legacy'),

    # 固定领域页（限定取值）
    re_path(r'^(?P<domain_id>' + _DOMAINS + r')/$',
            views.domain_detail, name='domain'),

    path('<slug:slug>/edit/', views.note_edit, name='edit'),
    path('<slug:slug>/save/', views.note_save, name='save'),
    path('<slug:slug>/', views.note_detail, name='detail'),
]
