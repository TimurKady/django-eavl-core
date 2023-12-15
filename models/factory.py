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
from .constants import FIELD_TYPES, VALIDATOR_TYPES, UNIQUE_SET


class BaseValueModel(models.Model):
    """
    Base model for storing attribute values with metadata.

    Attributes:
        meta_data (JSONField): JSON data containing metadata.
        value (JSONField): JSON data representing the attribute's value.
        timestamp (DateTimeField): Timestamp of when the record was created.
    """

    meta_data = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True
    )

    value = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.entity} - {self.attribute} - {self.timestamp}"

    def save(self, *args, **kwargs):
        if self.attribute.unique_set == UNIQUE_SET.globaly:
            # Check uniqueness globally
            if super().objects.filter(
                    attribute=self.attribute,
                    value=self.value).exists():
                raise ValueError(
                    "Value is not unique globally for this attribute.")
        elif self.attribute.unique_set == UNIQUE_SET.entity:
            # Check uniqueness within the entity
            if super().objects.filter(
                    entity=self.entity,
                    attribute=self.attribute,
                    value=self.value).exists():
                raise ValueError("Value is not unique within the entity for \
this attribute.")

        if self.attribute.schema.is_time_series:
            super().save(force_insert=True, *args, **kwargs)
        else:
            super().save(*args, **kwargs)


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
        attribute_model = type(model_name, (models.Model,), fields)

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
                on_delete=models.CASCADE
            ),
            attribute=models.ForeignKey(
                attribute_model,
                on_delete=models.CASCADE
            ),
            __module__=cls._meta.app_label,
            Meta=type('Meta', (object,), meta_dict),
        )

        # Create Values Model
        value_model = type(model_name, (models.Model,), fields)

        return value_model
