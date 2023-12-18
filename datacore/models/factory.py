# -*- coding: utf-8 -*-

"""
Dynamic Attribute and Value Model Factory for Django Entities.

This module provides a factory class, CoreFactory, that dynamically creates 
attribute and value models for Django entities. It ensures proper 
relationships between attribute and value models, checks their existence, 
and handles uniqueness constraints. Additionally, the module includes a 
base model, BaseValueModel, for storing attribute values with metadata.

Author: Timur Kady
Created on: Dec 15 2023
"""

import sys
from django.apps import apps
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _
from .constants import FIELD_TYPES, VALIDATOR_TYPES, UNIQUE_SET
from .schema import Schema


class BaseAttributeModel(models.Model):
    """
    Basic model for storing attribute definitions with metadata.
    Attributes:
        schema(models.ForeignKey): A reference to a foreign key to Schema.
        metadata(models.JSONField): JSON data containing metadata.
    """

    schema = models.ForeignKey(
        Schema,
        on_delete=models.CASCADE,
        verbose_name=_('Schema'),
    )

    meta_data = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        verbose_name=_('Metadata'),
    )

    class Meta:
        abstract = True

    def __str__(self):
        # String representation attribute name
        return f"{self.schema.title}"


class BaseValueModel(models.Model):
    """
    Base model for storing attribute values with metadata.
    Attributes:
        meta_data (models.JSONField): JSON data containing metadata.
        value (models.JSONField): JSON data representing the attribute's value.
        timestamp (models.DateTimeField): Timestamp of when the record was created.
    """

    meta_data = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        verbose_name=_('Metadata'),
    )

    value = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        verbose_name=_('Value')
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self):
        # String representation includes entity, attribute, and timestamp
        return f"{self.entity} - {self.attribute} - {self.timestamp}"

    def save(self, *args, **kwargs):
        # Check for global uniqueness of the value
        if self.attribute.unique_set == UNIQUE_SET.globaly and \
                self.__class__.objects.filter(attribute=self.attribute, value=self.value).exists():
            raise ValueError(
                _("Value is not unique globally for this attribute."))

        # Check for uniqueness within the entity
        elif self.attribute.unique_set == UNIQUE_SET.entity and \
                self.__class__.objects.filter(entity=self.entity, attribute=self.attribute, value=self.value).exists():
            raise ValueError(
                _("Value is not unique within the entity for this attribute."))

        # Check if all IDs in the relationship list exist in the entity model
        if self.attribute.schema.field_type == FIELD_TYPES.relationship and self.relationship:
            entity_class = self._meta.model
            valid_ids = set(entity_class.objects.filter(
                id__in=self.relationship).values_list('id', flat=True))
            if set(self.relationship) != valid_ids:
                raise ValueError(_("One or more IDs in the relationship do \
not exist in the Entity Model."))

        # Handling of time series data
        if self.attribute.schema.is_time_series:
            super(BaseValueModel, self).save(
                force_insert=True, *args, **kwargs)
        else:
            super(BaseValueModel, self).save(*args, **kwargs)


class CoreFactory(models.base.ModelBase):
    """
    Factory class for dynamically creating attribute and value models.

    This class creates attribute and value models for entities if they don't exist.
    It also ensures proper relationships between attribute and value models.

    Attributes:
        None
    """

    def __init__(cls, name, bases, dct):

        super().__init__(name, bases, dct)

        if not (cls._meta.get_parent_list() or cls._meta.abstract):

            name = cls._meta.object_name
            app_label = cls._meta.app_label

            attribute_model_name = f"{app_label}.{name}Attributes"
            value_model_name = f"{app_label}.{name}Values"

            # Check if the attribute model exists
            attribute_model = apps.get_model(
                attribute_model_name, require_ready=False
            )
            if attribute_model is None:
                # Create the attribute model if it doesn't exist
                attribute_model = cls.create_attribute_model()
                setattr(
                    sys.modules[app_label],
                    f"{name}Attributes",
                    attribute_model
                )

            # Check if the value model exists
            value_model = apps.get_model(value_model_name, require_ready=False)
            if value_model is None:
                # Create the value model if it doesn't exist
                value_model = cls.create_values_model(attribute_model)
                setattr(
                    sys.modules[app_label],
                    f"{name}Values",
                    value_model
                )

    @classmethod
    def create_attribute_model(cls):
        """
        Create an attribute model for the entity.

        Returns:
            attribute_model (models.Model): The newly created attribute model.
        """
        # Attribute Model Name
        model_name = '%sAttributes' % cls._meta.object_name

        # Attribute Model Meta fields
        meta_dict = dict(
            app_label=cls._meta.app_label,
            verbose_name='%s Attributes' % cls._meta.verbose_name,
        )

        # Attribute Model fields
        fields = dict(
            __module__=cls._meta.app_label,

            Meta=type('Meta', (object,), meta_dict),
        )

        # Create Attribute Model
        attribute_model = type(model_name, (BaseAttributeModel,), fields)

        return attribute_model

    @classmethod
    def create_values_model(cls, attribute_model):
        """
        Create a value model for the entity based on the attribute model.

        Args:
            attribute_model (models.Model): The attribute model for the entity.

        Returns:
            value_model (models.Model): The newly created value model.
        """
        # Values Model Name
        model_name = '%sValues' % cls._meta.object_name

        # Values Model Meta fields
        meta_dict = dict(
            app_label=cls._meta.app_label,
            verbose_name='%s Values' % cls._meta.verbose_name,
            indexes=[
                models.Index(fields=['entity', 'attribute']),
            ]
        )

        # Values Model fields
        fields = dict(
            entity=models.ForeignKey(
                cls,
                on_delete=models.CASCADE,
                related_name='values',
                verbose_name=_('Entity'),
            ),

            attribute=models.ForeignKey(
                attribute_model,
                related_name='values',
                on_delete=models.CASCADE,
                verbose_name=_('Attribute'),
            ),

            relationship=ArrayField(
                models.IntegerField(),
                default=list,
                verbose_name=_('Relationship'),
            ),

            __module__=cls._meta.app_label,

            Meta=type('Meta', (object,), meta_dict),
        )

        # Create Values Model
        value_model = type(model_name, (BaseValueModel,), fields)

        return value_model
