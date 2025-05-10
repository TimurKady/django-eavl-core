# -*- coding: utf-8 -*-

"""
Dynamic Entity, Attribute and Value Model Factory.

This module provides a factory class, BaseEntityClassModel, that dynamically
creates entity, attribute and value models.

It ensures proper relationships between models, checks their existence,
and handles uniqueness constraints.

Version: 0.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import sys
from django.db import models
from django.utils.translation import gettext_lazy as _

from .entity import AbstractEntityModel
from .attributes import AbstractAttributeModel
from .values import AbstractValueModel


class EntityFactoryMeta(models.Model):
    """Entity model factory (Entity/Attribute/Value)."""

    def __init__(cls, name, bases, dct):
        """Init."""
        super().__init__(name, bases, dct)
        if cls._meta.abstract or cls._meta.proxy or cls._meta.get_parent_list():
            return
        EntityFactoryMeta.create_models_for(cls)

    @staticmethod
    def create_models_for(cls, label: str = None):
        """Create models."""
        module = sys.modules[cls.__module__]
        base_name = cls._meta.object_name
        label = label or base_name.lower()

        # Prepare model names

        entity_name = f"{base_name}EntityModel"
        attr_name = f"{base_name}AttributeModel"
        value_name = f"{base_name}ValueModel"

        # Prepare fields

        # -- 1. EntityModel
        entity_fields = {
            "entity_type": models.ForeignKey(
                cls._meta.model,
                on_delete=models.CASCADE,
                null=False,
                blank=False,
                related_name='entity_set',
                verbose_name=_('Entity category'),
            ),
            "__module__": cls.__module__,
        }
        entity_meta = type('Meta', (), {
            "verbose_name": _(f"{label} entity"),
            "verbose_name_plural": _(f"{label} entities"),
        })
        entity_model = type(entity_name, (AbstractEntityModel,), {
            **entity_fields,
            "Meta": entity_meta,
        })
        setattr(module, entity_name, entity_model)

        # -- 2. AttributeModel
        attr_fields = {
            "entity": models.ForeignKey(
                entity_model,
                null=False,
                blank=False,
                on_delete=models.CASCADE,
                related_name="attributes",
                verbose_name=_('entity')
            ),
            "destination": models.ForeignKey(
                entity_model,
                null=True,
                blank=True,
                on_delete=models.CASCADE,
                related_name="sourse",
                verbose_name=_('link destination')
            ),
            "__module__": cls.__module__,
        }
        attr_meta = type('Meta', (), {
            "verbose_name": _(f"{label} attribute"),
            "verbose_name_plural": _(f"{label} attributes"),
        })
        attr_model = type(attr_name, (AbstractAttributeModel,), {
            **attr_fields,
            "Meta": attr_meta,
        })
        setattr(module, attr_name, attr_model)

        # -- 3. ValueModel
        value_fields = {
            "entity": models.ForeignKey(
                entity_model,
                null=False,
                blank=False,
                on_delete=models.CASCADE,
                related_name="value_set",
                verbose_name=_('entity')
            ),
            "attribute": models.ForeignKey(
                attr_model,
                null=False,
                blank=False,
                on_delete=models.CASCADE,
                related_name="values",
                verbose_name=_('attribute')
            ),
            "__module__": cls.__module__,
        }
        value_meta = type('Meta', (), {
            "verbose_name": _(f"{label} value"),
            "verbose_name_plural": _(f"{label} values"),
        })
        value_model = type(value_name, (AbstractValueModel,), {
            **value_fields,
            "Meta": value_meta,
        })
        setattr(module, value_name, value_model)

        return entity_model, attr_model, value_model


# The End
