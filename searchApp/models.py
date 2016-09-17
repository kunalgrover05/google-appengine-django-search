from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class IndexModel(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.IntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    processed = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
