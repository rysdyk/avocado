from django.db import models
from avocado.models import DataField

class CodedValue(models.Model):
    field = models.ForeignKey(DataField, related_name='coded_values+')
    value = models.CharField(max_length=100)
    coded = models.IntegerField()

    class Meta(object):
        app_label = 'avocado'
        unique_together = ('field', 'value')
        verbose_name = 'coded value'
        verbose_name_plural = 'coded values'
        ordering = ('value',)

    def natural_key(self):
        return self.field_id, self.value
