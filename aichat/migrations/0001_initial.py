# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, default='', max_length=120, verbose_name='标题')),
                ('backend', models.CharField(default='hermes', max_length=16, verbose_name='后端')),
                ('model', models.CharField(blank=True, default='', max_length=80, verbose_name='模型')),
                ('pinned', models.BooleanField(default=False, verbose_name='置顶')),
                ('archived', models.BooleanField(default=False, verbose_name='归档')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='最后活跃')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_conversations', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': 'AI 会话',
                'verbose_name_plural': 'AI 会话',
                'ordering': ('-pinned', '-updated_at'),
                'indexes': [models.Index(fields=['user', '-updated_at'], name='aichat_conv_user_upd_idx')],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('user', '用户'), ('assistant', '助手'), ('system', '系统')], default='user', max_length=16, verbose_name='角色')),
                ('content', models.TextField(blank=True, default='', verbose_name='内容')),
                ('attachments_json', models.TextField(blank=True, default='[]', verbose_name='附件(JSON)')),
                ('backend', models.CharField(blank=True, default='', max_length=16, verbose_name='后端')),
                ('model', models.CharField(blank=True, default='', max_length=80, verbose_name='模型')),
                ('error', models.BooleanField(default=False, verbose_name='是否出错')),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='时间')),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='aichat.conversation', verbose_name='会话')),
            ],
            options={
                'verbose_name': 'AI 消息',
                'verbose_name_plural': 'AI 消息',
                'ordering': ('id',),
                'indexes': [models.Index(fields=['conversation', 'id'], name='aichat_msg_conv_id_idx')],
            },
        ),
    ]
