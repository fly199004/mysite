# -*- coding: utf-8 -*-
"""后台管理：方便在 Django admin 里翻看/清理对话记录。"""
from django.contrib import admin
from django.db.models import Count

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ('role', 'content', 'created_at', 'error')
    readonly_fields = ('role', 'content', 'created_at', 'error')
    can_delete = True
    show_change_link = True


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'backend', 'model', 'updated_at', 'msg_count')
    list_filter = ('backend', 'archived', 'pinned')
    search_fields = ('title', 'user__username')
    raw_id_fields = ('user',)
    date_hierarchy = 'updated_at'
    inlines = [MessageInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(msg_count=Count('messages'))

    def msg_count(self, obj):
        return obj.msg_count
    msg_count.short_description = '消息数'
    msg_count.admin_order_field = 'msg_count'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'short', 'created_at')
    list_filter = ('role', 'error')
    search_fields = ('content',)
    raw_id_fields = ('conversation',)

    def short(self, obj):
        text = (obj.content or '').replace('\n', ' ')
        return text[:60] + ('…' if len(text) > 60 else '')
    short.short_description = '内容'
