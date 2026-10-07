from django.db import models


class Classroom(models.Model):
    """一个班级一条记录；完整页面状态以 JSON 文本存储在 state 字段。"""

    class_id = models.CharField('班级标识', max_length=64, unique=True, db_index=True)
    name = models.CharField('班级名称', max_length=100)
    state = models.TextField('状态JSON', default='{}')
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'classroom_room'
        verbose_name = '班级'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Current(models.Model):
    """单行表：记录当前选中的班级。"""

    key = models.CharField('键', max_length=32, unique=True, default='current')
    class_id = models.CharField('当前班级标识', max_length=64, blank=True, default='')

    class Meta:
        db_table = 'classroom_current'
        verbose_name = '当前班级'
        verbose_name_plural = verbose_name
