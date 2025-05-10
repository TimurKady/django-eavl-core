# -*- coding: utf-8 -*-
"""
Abstract Entity Model

This model provides common fields and behaviors for program entities.
Entities represent objects in a program and can be customized by inheriting
from this base class. It includes fields for UUID (Universally Unique
Identifier).

Version: 0.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import uuid
from django.db import models
from django.db.models import QuerySet
from treenode.models import TreeNodeModel
from django.utils.translation import gettext_lazy as _


class AbstractEntityModel(TreeNodeModel):
    """Base abstact model for entities."""

    entity_class = models.BigIntegerField()

    title = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        verbose_name=_('entity name'),
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name=_('UUID'),
        help_text=_('Universally Unique Identifier for this entity.'),
    )

    display_field = "title"
    sorting_field = "title"

    class Meta(TreeNodeModel.Meta):
        """Meta class."""

        abstract = True

    # == 1. Base methods

    def get_data(self, *, include_inherited=True) -> dict:
        """
        Return object data.

        Returns a dictionary with a full representation of the objects with its
        attributes, including those inherited from parent objects.
        """
        pass

    def set_data(self, data: dict, *, validate=True) -> None:
        """
        Set object data.

        Apply data to an object, updating attribute values.
        Validation can be disabled.
        """
        pass

    def validate_data(self, data: dict = None) -> None:
        """
        Validate object data.

        Check the validity (structural and substantive) of the input data or
        current data.
        """
        pass

    def apply_transaction(self, data: dict) -> object:  # "EntityModel"
        """
        Create or update an object.

        Atomic assembly of an object with all attributes/relationships.
        """
        pass

    def destroy(self, *, force=False) -> None:
        """
        Destoy object.

        Safely delete an object and all associated attributes and their values,
        with dependency checking.
        """
        pass

    def get_attributes(self) -> list:  # List[AttributeModel]
        """
        Get effective attributes.

        Get a list of all applicable attributes, including inherited ones.
        """
        all_attrs = []
        for node in reversed(self.get_ancestors()):
            for attr in node.attributes.all():
                all_attrs.append((attr.code, attr))

        seen = {}
        for code, attr in all_attrs:
            if code not in seen:
                seen[code] = attr

        return list(seen.values())[::-1]

    def get_attribute_value(self, code_or_title: str):
        """
        Get attribute value.

        Return the current value of a specific attribute.
        (taking into account polymorphism and multiplicity).
        """
        attrs = self.get_attributes()
        for node in attrs:
            if node.code == code_or_title or node.title == code_or_title:
                return node.values.filter(entity=self).all()
        return None

    def set_attribute_value(self, code: str, value: any) -> None:
        """Set a new value to an attribute (or attributes)."""
        pass

    def to_dict(self, include_links=True, include_values=True):
        """Return object by dict."""
        pass

        # == 2. Methods of working with links

    def get_outgoing_links(self, code: str = None) -> list:
        """Get a list of entities referenced by this object."""
        pass

    def get_incoming_links(self, code: str = None) -> list:
        """Return a list of entities that reference this object."""
        pass

    def has_direct_link_to(self, other: object, code: str = None) -> bool:
        """Check if there is a direct connection to another object."""
        pass

    def is_connected_to(self, other: object, max_depth: int = 3) -> bool:
        """Проверяет, связаны ли объекты через цепочку (до max_depth)."""
        pass

    def get_graph_subtree(self, depth: int = 1,
                          link_codes: list = None,
                          entity_types: list = None) -> dict:
        """
        Get graph subtree.

        Returns a subgraph in the form like:
        {
            entity_id: {
                "entity": <Entity>,
                "links": [<entity_id>, ...]
            },
            ...
        }
        """
        pass

    # == 3. Methods of objects searching and filtering

    @classmethod
    def search_by_attribute(cls, code: str, value: any) -> QuerySet:
        """
        Search by attribute value.

        Find all objects that have a value for a given attribute.
        """
        pass

    @classmethod
    def search_related_to(cls, other: object, via: str = None) -> QuerySet:
        """
        Search related objects.

        Find all objects associated with the passed object
        (via optional link code).
        """
        pass

    @classmethod
    def get_by_uuid(cls, uuid: str) -> object:
        """
        Get object be UUID.

        Quick search by UUID.
        """
        pass

    def find_link_path_to(self, target: object, *,
                          allowed_entity_types: set[str] = None,
                          allowed_link_codes: set[str] = None,
                          mode='first',  # mode='first' | 'all'
                          max_depth: int = 5,
                          return_objects=True) -> list:
        """
        Find a path through all links.

        allowed_entity_types: limits search by entity types;
        allowed_link_codes: limits the types of relationships;
        max_depth: search depth (limited to 5 nodes by default)

        Returns a list of entities (path), or None if the path is not found.
        """
        pass


# The ENd
