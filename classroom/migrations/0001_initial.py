"""课堂点名积分初始迁移"""
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Classroom',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('class_id', models.CharField(
                    db_index=True, max_length=64, unique=True, verbose_name='班级标识')),
                ('name', models.CharField(max_length=100, verbose_name='班级名称')),
                ('state', models.TextField(default='{}', verbose_name='状态JSON')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '班级',
                'verbose_name_plural': '班级',
                'db_table': 'classroom_room',
            },
        ),
        migrations.CreateModel(
            name='Current',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(
                    default='current', max_length=32, unique=True, verbose_name='键')),
                ('class_id', models.CharField(
                    blank=True, default='', max_length=64, verbose_name='当前班级标识')),
            ],
            options={
                'verbose_name': '当前班级',
                'verbose_name_plural': '当前班级',
                'db_table': 'classroom_current',
            },
        ),
    ]
