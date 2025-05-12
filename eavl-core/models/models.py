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
from treenode.models import TreeNodeModel


from .factory import EntityFactoryMeta
from .schemas import eavl_schemas


class AbstractEntityClassModel(TreeNodeModel, metaclass=EntityFactoryMeta):
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

    def __str__(self):
        """Rreturn object string."""
        return self.title

    def get_attributes_schemas(self):
        """Get attributes for an entity class."""
        ancestors = reversed(self.get_ancestors(include_self=True))
        schemas = set()
        for node in ancestors:
            schemas.add(node.schemas)
        return list(schemas)

    def make_migtstions(self):
        """Make migrations when changing the schemaы."""
        # TODO: make migrations.

    def create_entity(self, **kwards):
        """Create an entity."""
        entity_model = self.entities.model
        entity = entity_model.objects.create(**{
            "title": kwards.get("title", None),
            "entity_class": self,
        })
        entity.save()

        for schema in self.get_attributes_schemas():
            with self.entities.atrubutes.model as model:
                last_schema = self.get_last_schema(schema.name)
                options = {
                    "entity": entity,
                    "title": schema.title,
                    "code": last_schema,
                    "schema": schema,
                    "is_multiple": schema.get("many", False),
                    "is_relation": schema.get("type") == "link",
                }
                attribute = model.objects.create(**options)
                default = schema.get("default", None)
                if default:
                    attribute.set_value(default)
        return entity

    def save(self, *args, **kwargs):
        """Save instance."""
        if self.pk:
            # TODO: run migtations if schemas was changed.
            pass
        super().save()


# The End
