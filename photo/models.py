from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User
import os
from datetime import datetime
from .oss_utils import OssStorage

# Create your models here.


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='标签名')
    created = models.DateTimeField(default=now, verbose_name='创建时间')

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = verbose_name
        ordering = ['name']

    def __str__(self):
        return self.name


class Photo(models.Model):
    title = models.CharField(max_length=200, verbose_name='标题')
    description = models.TextField(verbose_name='描述', blank=True)
    image = models.ImageField(
        upload_to='', 
        verbose_name='图片'
    )
    created = models.DateTimeField(default=now, verbose_name='创建时间')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name='上传者', null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='标签')

    class Meta:
        verbose_name = '照片'
        verbose_name_plural = verbose_name
        ordering = ['-created']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.image:
            try:
                # 简化路径结构：username/year/filename
                current_year = str(datetime.now().year)
                file_name = os.path.basename(self.image.name)
                
                # 只使用用户名和年份构建路径
                object_name = f'{self.user.username}/{current_year}/{file_name}'
                
                # 上传文件到 OSS
                oss_storage = OssStorage()
                url = oss_storage.upload_file(self.image.file, object_name)
                print(f"File uploaded to OSS: {url}")
                
                # 只保存相对路径
                self.image.name = object_name
                
            except Exception as e:
                print(f"Error in OSS upload: {str(e)}")
                raise
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # 删除 OSS 上的文件
        if self.image:
            try:
                oss_storage = OssStorage()
                oss_storage.delete_file(self.image.name)
            except Exception as e:
                print(f"Error deleting from OSS: {str(e)}")
        
        super().delete(*args, **kwargs)

    def get_image_url(self):
        if self.image:
            # 从OssStorage获取完整URL
            oss_storage = OssStorage()
            return oss_storage.get_url(self.image.name)
        return ''

    def get_url(self):
        """获取图片的完整URL"""
        if self.image:
            oss_storage = OssStorage()
            return oss_storage.get_url(self.image.name)
        return ''

    def get_signed_url(self):
        """获取图片的签名URL"""
        if self.image:
            oss_storage = OssStorage()
            return oss_storage.get_signed_url(self.image.name)
        return ''

    def get_tags(self):
        """获取照片的所有标签"""
        return self.tags.all()