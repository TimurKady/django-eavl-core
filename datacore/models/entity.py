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
from django.utils.translation import gettext_lazy as _

from .objects import WrapObject


class AbstractEntityModel(models.Model):
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

    class Meta:
        """Meta class."""

        abstract = True

    # == 1. Base methods ==

    def get_data(self, *, last_only=True,
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
        attributes = self.attributes.filter(deleted=False)

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
            props_list = node.attributes.filter(is_relation=False, deleted=False)  # noqa: D501
            for prop in props_list:
                properties.append(prop.to_dict(include_values))

            if include_links:
                links_list = node.attributes.filter(is_relation=True, deleted=False)  # noqa: D501

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
            attr = self.attributes.filter(code=field, deleted=False).first()
            if attr:
                attr.set_value(value)

    # == 2. Clean and validation ==

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
                attr = self.attributes.filter(code=field, deleted=False).first()
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

    # == 3 Wrap methods ==

    def create_wrap(self) -> object:
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

    # == 4. Methods of working with links ==

    def get_outgoing_links(self, code: str = None) -> list:
        """Get a list of entities referenced by this object."""
        queryset = self.attributes.model.objects\
            .filter(entity=self, is_relation=True, deleted=False)
        return list(queryset.values_list("destination", flat=True))

    def get_incoming_links(self, code: str = None) -> list:
        """Return a list of entities that reference this object."""
        queryset = self.attributes.model.objects\
            .filter(is_relation=True, destination=self, deleted=False)
        return list([a.sourse for a in queryset])

    def has_direct_link_to(self, other: object, code: str = None) -> bool:
        """Check if there is a direct connection to another object."""
        links = self.get_outgoing_links()
        return other in links

    def is_connected_to(self, target, *, max_depth=6, visited=None):
        """
        Check if self is connected to target entity.

        DFS via a chain of relational attributes with a max_depth constraint.
        Parameters:
        - target: target entity instance
        - max_depth: maximum search depth (default: 6)
        - visited: set of already visited entities (for recursion)

        Returns:
        - True if a path exists from self to target via linked entities
        - False otherwise
        """
        visited = set()
        stack = [(self, 0)]  # (entity, current_depth)

        while stack:
            current, depth = stack.pop()

            if current.pk == target.pk:
                return True

            if current.pk in visited or depth >= max_depth:
                continue

            visited.add(current.pk)

            for attr in current.attributes.filter(is_relation=True):
                dest = attr.destination
                if dest and dest.pk not in visited:
                    stack.append((dest, depth + 1))

        return False

    def get_graph_subtree(self, depth: int = 1, link_codes: list = None,
                          entity_types: list = None) -> dict:
        """
        Get graph subtree.

        Returns a semantic subgraph rooted at this entity,
        traversing relation-attributes (is_relation=True) up to a given depth.

        :param depth: Max search depth.
        :param link_codes: Optional list of attribute codes to follow.
        :param entity_types: Optional list of allowed entity_class UUIDs.
        :return: Dict with structure
            {
                entity_id: {
                    "entity": Entity,
                    "links": [entity_id, ...]
                },
                ...
            }
        """
        from collections import deque

        graph = {}
        visited = set()
        stack = deque()
        stack.append((self, 0))

        while stack:
            current, d = stack.pop()
            if current.pk in visited or d > depth:
                continue

            visited.add(current.pk)
            links = []

            for attr in current.attributes.filter(is_relation=True):
                if link_codes and attr.code not in link_codes:
                    continue

                dest = attr.destination
                if not dest or dest.pk in visited:
                    continue

                if entity_types:
                    etype = getattr(dest.entity_class, "uuid",
                                    dest.entity_class_id)
                    if etype not in entity_types:
                        continue

                links.append(dest.pk)
                stack.append((dest, d + 1))

            graph[current.pk] = {
                "entity": current,
                "links": links
            }

        return graph

    # == 5. Methods of objects searching and filtering ==

    @classmethod
    def search_by_attribute(cls, code: str, value: any) -> QuerySet:
        """
        Search by attribute value.

        Find all objects of this class that have the specified value
        for the attribute with the given code.

        :param code: Attribute code.
        :param value: Value to search for.
        :return: QuerySet of matching entities.
        """
        attr_model = cls.attributes.model

        attr_qs = attr_model.objects.filter(
            code=code,
            value=value,
            entity__entity_class=cls.entity_class,
            deleted=False
        )

        entity_ids = attr_qs.values_list("entity", flat=True).distinct()
        return cls.objects.filter(pk__in=entity_ids)

    @classmethod
    def search_related_to(cls, other: object, via: str = None) -> QuerySet:
        """
        Search related objects.

        Find all objects of this class that are related to the given object
        via attribute-based relations (is_relation=True).

        :param other: The target entity being referenced.
        :param via: Optional code of the link-attribute.
        :return: QuerySet of related entities (instances of cls).
        """
        attr_qs = cls.attributes.model.objects.filter(
            is_relation=True,
            destination=other,
            entity__entity_class=cls.entity_class,
            deleted=False
        )

        if via:
            attr_qs = attr_qs.filter(code=via)

        entity_ids = attr_qs.values_list("entity", flat=True).distinct()

        return cls.objects.filter(pk__in=entity_ids)

    @classmethod
    def get_by_uuid(cls, uuid: str) -> object:
        """
        Get object by UUID.

        Quick search by UUID.
        """
        return cls.objects.filter(uuid=uuid).first()

    def find_link_path_to(self, target: object, *,
                          allowed_entity_types: set[str] = None,
                          allowed_link_codes: set[str] = None,
                          mode: str = 'first',
                          max_depth: int = 6,
                          return_objects: bool = True) -> list | None:
        """
        Find a path through link-attributes tothe target entity.

        :param target: Target entity to search path to.
        :param allowed_entity_types: Limit traversal to certain entity class
            IDs (or UUIDs).
        :param allowed_link_codes: Limit traversal to certain attribute codes.
        :param mode: 'first' to stop at first found path, 'all' to find all
            paths.
        :param max_depth: Maximum depth of search.
        :param return_objects: Whether to return actual entity objects or their
            UUIDs.
        :return: List of entity path (from self to target), or None if
            not found.

        Examples:
        entity.find_link_path_to(target, max_depth=5)
        entity.find_link_path_to(target, allowed_link_codes={"parent", "child"})
        entity.find_link_path_to(
            target,
            allowed_entity_types={"product", "department"},
            return_objects=False
        )

        """
        from collections import deque

        visited = set()
        stack = deque()
        paths = []

        # Each stack item: (current_entity, path_so_far)
        stack.append((self, [self]))

        while stack:
            current, path = stack.pop()

            if current.pk == target.pk:
                result_path = path if return_objects else [e.uuid for e in path]
                if mode == 'first':
                    return result_path
                else:
                    paths.append(result_path)
                    continue

            if current.pk in visited or len(path) > max_depth:
                continue
            visited.add(current.pk)

            rel_attrs = current.attributes.filter(
                is_relation=True).exclude(destination=None)

            for attr in rel_attrs:
                if allowed_link_codes and attr.code not in allowed_link_codes:
                    continue
                dest = attr.destination
                if not dest:
                    continue
                if allowed_entity_types:
                    type_id = dest.entity_class.uuid
                    if type_id not in allowed_entity_types:
                        continue
                if dest.pk not in visited:
                    stack.append((dest, path + [dest]))

        return paths if mode == 'all' else None

    # == 6. Migrations ==

    def add_attribute(self, schema):
        """Add attribute to self."""
        model = self.attributes.model
        options = {
            "entity": self,
            "title": schema.title,
            "code": schema.name,
            "schema": schema,
            "is_multiple": schema.get("many", False),
            "is_relation": schema.get("type") == "link",
        }
        attribute = model.objects.create(**options)
        default = schema.get("default", None)
        if default:
            attribute.set_value(default)

    def update_attribute(self, schema):
        """Update attribute."""
        # TODO: update attributes according to schema changes
        pass

    def remove_attribute(self, schema):
        """Remove attributes."""
        self.attributes.filter(code=schema.name, deleted=False).update(deleted=True)  # noqa: D501

# The End
