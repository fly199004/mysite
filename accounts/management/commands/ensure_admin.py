"""确保默认管理员账号 fei 存在（密码 fei）。
仅在该账号不存在时创建；若已存在（可能已改密码），不做覆盖。"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '初始化默认超级管理员账号 fei / fei（仅在不存在时创建）'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='fei')
        parser.add_argument('--password', default='fei')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        user = User.objects.filter(username=username).first()
        if user:
            self.stdout.write(self.style.WARNING(
                f'管理员账号 {username} 已存在，保留现有密码，未做改动。'))
            return
        User.objects.create_superuser(
            username=username, email='', password=password)
        self.stdout.write(self.style.SUCCESS(
            f'已创建超级管理员：{username} / {password}，请尽快登录后修改密码。'))
