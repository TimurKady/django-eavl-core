# -*- coding: utf-8 -*-
"""
Abstract Value Model.

Version: 0.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


import json
import requests
from django.db import models
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _
from marshmallow import Schema


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

    def clean_fields(self, exclude=None):
        """Validate all fields on value model."""
        schema_dict = self.attribute.schema
        is_url = "$ref" in schema_dict.keys()
        if is_url:
            url = schema_dict["$ref"]
            schema_dict = requests.get(url).json()
        schema = Schema.from_dict(schema_dict)
        errors = schema.validate(self.value)
        if errors:
            raise ValidationError(errors)

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
