# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""


Author: Timur Kady
Created on: Dec 15 2023
"""

import uuid
from django.db import models
from treenode.models import TreeNodeModel
from six import with_metaclass
from .factory import CoreFactory
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _


class Entity(with_metaclass(CoreFactory, models.Model)):
    """
    Base model for program entities with common fields and behaviors.

    This model provides common fields and behaviors for program entities.
    Entities represent objects in a program and can be customized by inheriting
    from this base class. It includes fields for UUID (Universally Unique 
    Identifier) and metadata.

    Attributes:
        uuid (UUIDField): Universally Unique Identifier for the entity.
        metadata (JSONField): JSON data for storing additional metadata.

    Meta:
        abstract (bool): Set to True to indicate that this is an abstract base
            model and should not be used to create database tables directly.

    Methods:
        __str__(): Returns a string representation of the entity, which is its UUID.

    Usage:
        To create custom program entities, inherit from this base class and
        add any additional fields or methods as needed.

    Example:
        class CustomEntity(Entity):
            # Additional fields and methods can be added here.
    """

    uuid = models.UUIDField(
        unique=True,
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        verbose_name=_('UUID'),
    )

    metadata = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        verbose_name=_('Metadata'),
    )

    class Meta:
        indexes = [
            models.Index(fields=['uuid']),
        ]
        abstract = True

    def __str__(self):
        """
        Returns a string representation of the entity, which is its UUID.

        Returns:
            str: The UUID of the entity as a string.
        """
        return str(self.uuid)
