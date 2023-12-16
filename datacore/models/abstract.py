# -*- coding: utf-8 -*-
"""
Author: Timur Kady
Created on: Dec 15, 2023
"""

import uuid
from django.db import models
from treenode.models import TreeNodeModel
from six import with_metaclass
from .factory import CoreFactory
from .schema import Schema
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _


class EntityCategories(TreeNodeModel):
    """
    Model representing categories for program entities.

    Categories are used to group and classify program entities. Each category
    has a name and an optional description. Entities can be associated with
    one or more categories through a many-to-many relationship with the Schema
    model.

    Attributes:
        name (CharField): The name of the category.
        description (TextField, optional): A description of the category.

    Meta:
        abstract (bool): Set to True to indicate that this is an abstract base
            model and should not be used to create database tables directly.

    Usage:
        To create custom categories for program entities, inherit from this
        base class and add any additional fields or methods as needed.
    """

    name = models.CharField(
        max_length=255,
        verbose_name=_('Category name'),
        help_text=_('Give this category a name.'),
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Give a description of this category. Determine what '
                    'entities will be included in it.'),
    )

    schemas = models.ManyToManyField(
        Schema,
        related_name='categories',
        verbose_name=_('Associated Schemas'),
        help_text=_('Select the schemas associated with this category.'),
    )

    class Meta:
        abstract = True


class Entity(with_metaclass(CoreFactory, models.Model)):
    """
    Base model for program entities with common fields and behaviors.

    This model provides common fields and behaviors for program entities.
    Entities represent objects in a program and can be customized by inheriting
    from this base class. It includes fields for UUID (Universally Unique 
    Identifier) and metadata.

    Attributes:
        entity_type (ForeignKey): The category or type of the entity.
        uuid (UUIDField): Universally Unique Identifier for the entity.
        metadata (JSONField, optional): JSON data for storing additional metadata.

    Meta:
        indexes (list): Index definition for the UUID field.
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

    entity_type = models.ForeignKey(
        EntityCategories,
        on_delete=models.CASCADE,
        related_name='entities',
        verbose_name=_('Entity category'),
        help_text=_('Select the category for this entity.'),
    )

    uuid = models.UUIDField(
        unique=True,
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        verbose_name=_('UUID'),
        help_text=_('Universally Unique Identifier for this entity.'),
    )

    metadata = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional metadata for this entity in JSON format.'),
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
