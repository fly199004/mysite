from djongo import models
from bson import ObjectId

class Article(models.Model):
    _id = models.ObjectIdField()  # MongoDB中的ObjectId
    title = models.CharField(max_length=255)
    content = models.TextField()
    tags = models.JSONField()  # 假设tags是一个数组
    top = models.IntegerField(default=0)
    category = models.CharField(max_length=100)
    hidden = models.BooleanField(default=False)
    author = models.CharField(max_length=100)
    pathname = models.CharField(max_length=255, blank=True)
    private = models.BooleanField(default=False)
    password = models.CharField(max_length=255, blank=True)
    deleted = models.BooleanField(default=False)
    viewer = models.IntegerField(default=0)
    visited = models.IntegerField(default=0)
    createdAt = models.DateTimeField()
    updatedAt = models.DateTimeField()
    lastVisitedTime = models.DateTimeField()

    def __str__(self):
        return self.title


