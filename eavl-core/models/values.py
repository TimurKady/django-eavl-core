# -*- coding: utf-8 -*-
"""
Abstract Value Model.

Version: 0.0.1
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _


class AbstractValueModel(models.Model):
    """Base model for storing attribute values."""

    entity = models.BigIntegerField()
    attribute = models.BigIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    value = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        verbose_name=_('value'),
        unique_for_date="timestamp"
    )

    class Meta:
        """Meta class."""

        abstract = True
        indexes = [models.Index(fields=["entity", "attribute"]),]
        order_with_respect_to = "attribute"
        ordering = ["-timestamp"]

    def __str__(self):
        """Represent object by string."""
        return f"{str(self.value)} ({self.timestamp})"

    def delete(self):
        """Delete instance."""
        if self.attribute.is_timeseries:
            return
        super().delete()

    def save(self, force_insert=False, force_update=False,  *args, **kwargs):
        """Save instance."""
        force_insert = self.attribute.is_timeseries
        force_update = not self.attribute.is_timeseries
        # self.clean_fields()
        super().save(force_insert, force_update,  *args, **kwargs)


# The End
