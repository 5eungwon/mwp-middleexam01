import uuid
from pathlib import Path
from django.conf import settings
from django.db import models


def image_path(instance, filename):
    return f'photos/{uuid.uuid4().hex}{Path(filename).suffix.lower()}'


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=100)
    text = models.TextField(blank=True, max_length=2000)
    image = models.ImageField(upload_to=image_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.title
