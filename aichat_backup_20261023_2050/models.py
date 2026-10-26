# -*- coding: utf-8 -*-
"""AI 对话数据模型：会话 + 消息，按用户隔离，服务端持久化。"""
import json

from django.conf import settings
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    """一次完整的对话（左侧列表里的一条）。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='ai_conversations', verbose_name='用户',
    )
    title = models.CharField('标题', max_length=120, blank=True, default='')
    backend = models.CharField('后端', max_length=16, default='hermes')
    model = models.CharField('模型', max_length=80, blank=True, default='')
    pinned = models.BooleanField('置顶', default=False)
    archived = models.BooleanField('归档', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('最后活跃', default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'AI 会话'
        verbose_name_plural = 'AI 会话'
        ordering = ('-pinned', '-updated_at')
        indexes = [models.Index(fields=['user', '-updated_at'])]

    def __str__(self):
        return '%s · %s' % (self.user_id, self.title or '新对话')

    def touch(self, title=None):
        self.updated_at = timezone.now()
        fields = ['updated_at']
        if title and self.title != title:
            self.title = title[:120]
            fields.append('title')
        self.save(update_fields=fields)

    def as_dict(self):
        return {
            'id': self.id,
            'title': self.title or '新对话',
            'backend': self.backend,
            'model': self.model,
            'pinned': self.pinned,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': getattr(self, 'message_count', None),
        }


class Message(models.Model):
    """会话里的一条消息。attachments 用 TextField 存 JSON，兼容 MySQL/MariaDB/SQLite。"""

    ROLE_CHOICES = (
        ('user', '用户'),
        ('assistant', '助手'),
        ('system', '系统'),
    )

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE,
        related_name='messages', verbose_name='会话',
    )
    role = models.CharField('角色', max_length=16, choices=ROLE_CHOICES, default='user')
    content = models.TextField('内容', blank=True, default='')
    attachments_json = models.TextField('附件(JSON)', blank=True, default='[]')
    backend = models.CharField('后端', max_length=16, blank=True, default='')
    model = models.CharField('模型', max_length=80, blank=True, default='')
    error = models.BooleanField('是否出错', default=False)
    created_at = models.DateTimeField('时间', default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'AI 消息'
        verbose_name_plural = 'AI 消息'
        ordering = ('id',)
        indexes = [models.Index(fields=['conversation', 'id'])]

    def __str__(self):
        return '%s #%s %s' % (self.conversation_id, self.id, self.role)

    @property
    def attachments(self):
        try:
            data = json.loads(self.attachments_json or '[]')
            return data if isinstance(data, list) else []
        except Exception:
            return []

    @attachments.setter
    def attachments(self, value):
        self.attachments_json = json.dumps(value or [], ensure_ascii=False)

    def as_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'attachments': self.attachments,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
        }
