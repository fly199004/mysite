import oss2
from django.conf import settings
import os
import time

class OssStorage:
    def __init__(self):
        self.auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(
            self.auth, 
            settings.OSS_ENDPOINT, 
            settings.OSS_BUCKET_NAME
        )

    def upload_file(self, file_obj, object_name=None):
        if object_name is None:
            object_name = file_obj.name

        try:
            # 上传文件
            result = self.bucket.put_object(object_name, file_obj)
            
            # 生成签名URL，有效期1小时
            url = self.bucket.sign_url('GET', object_name, 60 * 60)
            return url
            
        except Exception as e:
            print(f"Upload error: {str(e)}")
            raise

    def get_signed_url(self, object_name):
        """获取文件的签名URL"""
        try:
            url = self.bucket.sign_url('GET', object_name, 60 * 60)  # 1小时有效期
            return url
        except Exception as e:
            print(f"Error generating signed URL: {str(e)}")
            raise

    def get_url(self, object_name):
        """获取文件的完整URL"""
        return f"{self.base_url}/{object_name}"

    def delete_file(self, object_name):
        """
        从 OSS 删除文件
        :param object_name: OSS中的文件名
        """
        try:
            self.bucket.delete_object(object_name)
        except Exception as e:
            print(f"Delete error: {str(e)}")
            raise

    def list_files(self):
        """获取OSS中的所有文件列表"""
        bucket = self.get_bucket()
        files = []
        
        # 列举文件
        for obj in oss2.ObjectIterator(bucket):
            if not obj.key.endswith('/'):  # 排除目录
                files.append(obj.key)
                
        return files
