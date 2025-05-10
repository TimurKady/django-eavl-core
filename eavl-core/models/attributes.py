# -*- coding: utf-8 -*-
"""
Abstract Attribute Model.

Version: 0.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import uuid
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _


class AbstractAttributeModel(models.Model):
    """Abstract Attribute Model"""

    entity = models.BigIntegerField()

    title = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        verbose_name=_('attribute name'),
    )

    code = models.SlugField(
        null=False,
        blank=False,
        db_index=True,
        verbose_name=_('code'),
        help_text=_('Attribute internal code/name'),
    )

    schema = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Schema'),
        encoder=DjangoJSONEncoder,
        help_text=_('The attribute data schema. '
                    'Can be specified as a URL to a JSON dictionary '
                    'of the schema.'),
    )

    is_multiple = models.BooleanField(
        default=False,
        verbose_name=_('is multiple'),
        help_text=_('Whether to treat data as a collection by default.')
    )

    is_relation = models.BooleanField(
        default=False,
        verbose_name=_('is a link'),
        help_text=_('Whether to treat data as a lınk by default.')
    )

    destination = models.BigIntegerField()

    is_timeseries = models.BooleanField(
        default=False,
        verbose_name=_('is a time series'),
        help_text=_('Whether to treat data as  a time series by default.')
    )

    class Meta:
        """Meta class."""

        abstract = True
        ordering = ["title"]
        unique_together = [["entity", "code"]]

    def __str__(self):
        """Return a string representation of the entity."""
        return f"{self.title} ({self.code})"


# The End
