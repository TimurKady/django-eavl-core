# -*- coding: utf-8 -*-
"""
Abstract Entity Class Model.

Categories are used to group and classify entities. Each category
has a name (title) and an optional description. Entities can be associated
with one class (category).

Version: 0.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


from .factory import EntityFactoryMeta


class AbstractEntityClassModel(models.Model, metaclass=EntityFactoryMeta):
    """Classes (categories) for entities."""

    title = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        verbose_name=_('Category name'),
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Give a description of this category. Determine what '
                    'entities will be included in it.'),
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name=_('UUID'),
        help_text=_('Universally Unique Identifier for this entity.'),
    )

    class Meta:
        """EntityClass Meta class."""

        abstract = True
        ordering = ["title"]
        verbose_name = _("entity class")
        verbose_name_plural = _("entity classes")

    def __str__(self):
        """Rreturn object string."""
        return self.title
