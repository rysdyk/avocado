from django.db import models
from .query import CacheQuerySet


class CacheManager(models.Manager):
    def get_queryset(self):
        return CacheQuerySet(self.model)
