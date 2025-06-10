# -*- coding: utf-8 -*-
"""
Abstract Entity Class Model.

Categories are used to group and classify entities. Each category
has a name (title) and an optional description. Entities can be associated
with one class (category).

Version: 0.0.1
Author: Timur Kady
Email: timurkady@yandex.com
"""


import threading
import sys
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from treenode.models import TreeNodeModel

from .schemas import eavl_schemas
from .entity import AbstractEntityModel
from .attributes import AbstractAttributeModel
from .values import AbstractValueModel


_lock = threading.Lock()


class AbstractEntityClassModel(TreeNodeModel):
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

    schemas = models.ManyToManyField(
        eavl_schemas,
        blank=True,
        null=True,
        related_name="classes",
        verbose_name="Avable attributes"
    )

    display_field = "title"
    sorting_field = "title"

    class Meta(TreeNodeModel.Meta):
        """EntityClass Meta class."""

        abstract = True
        verbose_name = _("entity class")
        verbose_name_plural = _("entity classes")

    def __init_subclass__(cls, **kwargs):
        """Init class."""
        super().__init_subclass__(**kwargs)
        if cls._meta.abstract or cls._meta.proxy or cls._meta.get_parent_list():
            return
        models = cls.create_models_for()
        setattr(cls, "entity_model", models[0])
        setattr(cls, "attr_model", models[1])
        setattr(cls, "value_model", models[2])
        setattr(models[0], "entity_class", cls)

    def __str__(self):
        """Rreturn object string."""
        return self.title

    @classmethod
    def create_models_for(cls):
        """Create models."""
        with _lock:
            module = sys.modules[cls.__module__]
            base_name = cls._meta.object_name
            readable_name = cls._meta.object_name.replace('_', ' ')

            # Prepare model names

            entity_name = f"{base_name}EntityModel"
            attr_name = f"{base_name}AttributeModel"
            value_name = f"{base_name}ValueModel"

            # Prepare fields

            # -- 1. EntityModel
            entity_fields = {
                "entity_class": models.ForeignKey(
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
                "verbose_name": _(f"Entity ({readable_name})"),
                "verbose_name_plural": _(f"Entities ({readable_name})"),
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
                "verbose_name": _(f"Attribute ({readable_name})"),
                "verbose_name_plural": _(f"Attribute ({readable_name})"),
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
                "indexes": [models.Index(fields=["timestamp"])],
                "verbose_name": _(f"Value ({readable_name})"),
                "verbose_name_plural": _(f"Value ({readable_name})"),
            })
            value_model = type(value_name, (AbstractValueModel,), {
                **value_fields,
                "Meta": value_meta,
            })
            setattr(module, value_name, value_model)

        return entity_model, attr_model, value_model

    def create_entity(self, **kwards):
        """Create an entity."""
        # Create new entity
        entity_model = self.entities.model
        entity = entity_model.objects.create(**{
            "title": kwards.get("title", None),
            "entity_class": self,
        })
        entity.save()

        # Add attributes to entity
        for schema in self.get_attributes_schemas():
            entity.addadd_attribute(schema)
        return entity

    def get_attributes_schemas(self):
        """Get attributes for an entity class."""
        ancestors = reversed(self.get_ancestors(include_self=True))
        schemas = set()
        for node in ancestors:
            schemas.add(node.schemas.all())
        return list(schemas)

    def make_migrations(self, added=None, removed=None, updated=None):
        """
        Make attribute data migration when changing the data schema.

        Migrate attribute values ​​from the old schema to the new one:
        - for attributes that match by code, FK is updated
        - for those that are missing in the new schema, make delete
        """
        entities_list = list[self.entities.all()]
        for entity in entities_list:
            all_names = added + removed + updated
            for schema in self.schemas.filter(name__in=all_names):
                if schema.name in added:
                    entity.add_attribute(schema)
                elif schema.name in updated:
                    entity.update_attribute(schema)
                else:
                    entity.remove_attribute(schema)

    def diff_schemas(self, old_schemas, new_schemas):
        """
        Compare two schemas.

        Compare two schema sets from .schemas.all(), and return:
        - added: set of schema names that are new
        - removed: set of schema names that were removed
        - updated: set of schema names that changed version
        """
        old_map = {sh.name: sh.version for sh in old_schemas}
        new_map = {sh.name: sh.version for sh in new_schemas}

        old_names = set(old_map)
        new_names = set(new_map)

        added = new_names - old_names
        removed = old_names - new_names
        common = old_names & new_names

        updated = {name for name in common if old_map[name] != new_map[name]}

        return added, removed, updated

    def save(self, *args, **kwargs):
        """
        Save instance.

        If 'schemas' field has changed compared to the previous version,
        determine which new schemas were added, and trigger migrations
        accordingly.
        """
        if self.pk:
            old = self._meta.model.objects.get(pk=self.pk)

            if self.schemas != old.schemas:
                added, removed, updated = self.diff_schemas(
                    old.schemas.all(),
                    self.schemas.all()
                )

                if added or removed or updated:
                    self.make_migrations(
                        added=added,
                        removed=removed,
                        updated=updated
                    )

        super().save(*args, **kwargs)

    @classmethod
    def clean_db(cls):
        """Clean DB from deleted attributes and values."""
        cls.attr_model.objects.filter(deleted=True).delete()

# The End
