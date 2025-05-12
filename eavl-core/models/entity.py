# -*- coding: utf-8 -*-
"""
Abstract Entity Model

This model provides common fields and behaviors for program entities.
Entities represent objects in a program and can be customized by inheriting
from this base class. It includes fields for UUID (Universally Unique
Identifier).

Version: 0.0.1
Author: Timur Kady
Email: timurkady@yandex.com
"""

import uuid
from django.db import models
from django.db.models import QuerySet
from treenode.models import TreeNodeModel
from django.utils.translation import gettext_lazy as _

from .objects import WrapObject


class AbstractEntityModel(TreeNodeModel):
    """Base abstract model for entities."""

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

    # == 1. Base methods ==

    @classmethod
    def create_entity(cls, **kwards):
        """Create a new entity instance."""
        entity_class = kwards.get("entity_class", None)

        # Create base object
        fields = {
            "entity_class": entity_class,
            "parent": kwards.get("parent", None),
            "title": kwards.get("title", None),
        }

        entity = cls(**fields)
        entity.save()

        # Inherited attrutes installation.
        attributes = entity.get_attributes()
        for attr in attributes:
            schema = attr.schema or {}

            entity.attributes._meta.objects.create(
                entity=entity,
                title=schema.get("title", None),
                code=attr.code,
                is_multiple=schema.get("many"),
                is_relation=schema.get("type") == "link",
            )

            default = schema.get("default", None)
            if default is not None:
                attr.set_value(default)

    def get_data(self, *, include_inherited=True, last_only=True,
                 from_date=None, to_date=None) -> dict:
        """
        Return object data.

        Returns a dictionary with a full representation of the object
        and its attribute values (including inherited ones if requested).

        Parameters:
        - include_inherited: whether to include attributes from parent nodes
        - last_only: for timeseries only, return only the latest value(s)
        - from_date, to_date: filter values by timestamp range (for timeseries)
        """
        attributes = (
            self.get_attributes()
            if include_inherited else self.attributes.all()
        )

        data = {
            "type": str(getattr(self.entity_class, "uuid", self.entity_class)),
            "uuid": str(self.uuid),
            "attributes": {}
        }

        for attr in attributes:
            data["attributes"].update({
                attr.code: attr.get_value(
                    last_only=last_only,
                    from_date=from_date,
                    to_date=to_date
                )
            })

        return data

    def to_dict(self, include_links=True, include_values=True):
        """Return object as dictionary with properties and links."""
        properties = []
        links = []

        for node in reversed(self.get_ancestors(include_self=True)):
            props_list = node.attributes.filter(is_relation=False)
            for prop in props_list:
                properties.append(prop.to_dict(include_values))

            if include_links:
                links_list = node.attributes.filter(is_relation=True)
                for link in links_list:
                    links.append(link.to_dict(include_values))

        result = {
            "type_id": self.entity_class_id,
            "title": self.title,
            "uuid": self.uuid,
            "properties": properties,
        }

        if include_links:
            result.update({"links": links})

        return result

    def set_data(self, data: dict, *, validate=True) -> None:
        """
        Set object data.

        Apply data to an object, updating attribute values.
        Validation can be disabled.
        """
        if validate:
            errors = self.validate(data)
            if errors:
                return errors

        attributes = data.get("attributes", {})
        for field, value in attributes.items():
            attr = self.attributes.filter(code=field).first()
            if attr:
                attr.set_value(value)

    def validate(self, data: dict = None, exclude: set = None) -> list:
        """
        Validate object data.

        Check the validity (structural and substantive) of the input data or
        current data.

        Data format expected same as from get_data().
        """
        errors = []
        exclude = exclude or set()
        attributes = data.get("attributes", {})
        for field, value in attributes.items():
            if field not in exclude:
                attr = self.attributes.filter(code=field).first()
                if attr:
                    schema = attr.get_schema()
                    result = schema.validate(value)
                    if result:
                        errors.append({field: result})

        return errors

    def clean(self):
        """Validate and modify model attributes."""
        pass

    def clean_fields(self, exclude: set = None) -> None:
        """
        Validate all model fields.

        Check the validity (structural and substantive) of the input data or
        current data.
        """
        super().clean_fields(exclude)

    def create_wrap(self, data: dict) -> object:
        """
        Create an object from EAVL.

        Atomic assembly of an object with all attributes/relationships.
        """
        return WrapObject(entity=self)

    def destroy_wrap(self, *, force=False) -> None:
        """
        Destroy object.

        Safely delete an object and all associated attributes and their values,
        with dependency checking.
        """
        # TODO: check incoming links
        # TODO: delete associated ValueModel records
        # TODO: recursively destroy descendants?
        self.delete()

    def get_attributes(self) -> list:
        """
        Get effective attributes.

        Get a list of all applicable attributes, including inherited ones.
        """
        all_attrs = []
        for node in reversed(self.get_ancestors(include_self=True)):
            for attr in node.attributes.all():
                all_attrs.append((attr.code, attr))

        seen = {}
        for code, attr in all_attrs:
            if code not in seen:
                seen[code] = attr

        return list(seen.values())[::-1]

    # == 2. Methods of working with links ==

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
        """Check whether objects are connected by a path (up to max_depth)."""
        pass

    def get_graph_subtree(self, depth: int = 1,
                          link_codes: list = None,
                          entity_types: list = None) -> dict:
        """
        Get graph subtree.

        Returns a subgraph in the form:
        {
            entity_id: {
                "entity": <Entity>,
                "links": [<entity_id>, ...]
            },
            ...
        }
        """
        pass

    # == 3. Methods of objects searching and filtering ==

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
        Get object by UUID.

        Quick search by UUID.
        """
        pass

    def find_link_path_to(self, target: object, *,
                          allowed_entity_types: set[str] = None,
                          allowed_link_codes: set[str] = None,
                          mode='first',  # mode='first' | 'all'
                          max_depth: int = 6,
                          return_objects=True) -> list:
        """
        Find a path through all links.

        allowed_entity_types: limits search by entity types;
        allowed_link_codes: limits the types of relationships;
        max_depth: search depth (limited to 6 nodes by default)

        Returns a list of entities (path), or None if the path is not found.
        """
        pass


# The End
