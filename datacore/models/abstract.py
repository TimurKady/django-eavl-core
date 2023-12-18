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
from django.db import connection


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

    def get_attribute_names(self, all=False):
        """
        Returns a list of attribute names for this entity.

        Parameters:
        all (bool): If True, returns all attribute names from related schemas.
                    If False, returns only those attributes that have values.
        """
        attribute_names = set()

        if all:
            # Get all attribute names from related schemas
            for schema in self.entity_type.schemas.all():
                for attribute in schema.attribute_model.all():  # Replace with the correct related name
                    attribute_names.add(attribute.name)
        else:
            # Get attribute names that have values
            for value in self.values.all():
                attribute_names.add(value.attribute.name)

        return list(attribute_names)

    def get_value(self, attribute_name, start_date=None, end_date=None):
        """
        Returns the value(s) of a given attribute for this entity.

        Parameters:
        attribute_name (str): The name of the attribute.
        start_date (datetime, optional): The start date for filtering the time 
        series.
        end_date (datetime, optional): The end date for filtering the time 
        series.
        """
        # Find the attribute model through the related schemas
        for schema in self.entity_type.schemas.all():
            if schema.name == attribute_name:
                # Assuming this is the reverse relation to the attribute model
                attribute = schema.attribute_model
                break
        else:
            return None  # Attribute not found

        # Filter values by date if provided
        values_queryset = self.values.filter(attribute=attribute)
        if start_date or end_date:
            values_queryset = values_queryset.filter(
                timestamp__gte=start_date, timestamp__lte=end_date)

        # Return the most recent value or all values within the date range
        return values_queryset.order_by('-timestamp').first().value if not start_date and not end_date else values_queryset.values_list('value', flat=True)

    def set_value(self, attribute_name, value, timestamp=None):
        """
        Sets the value of a given attribute for this entity.

        Parameters:
        attribute_name (str): The name of the attribute.
        value: The value to set for the attribute.
        timestamp (datetime, optional): The timestamp for the value, required 
        for time series attributes.
        """
        # Find the attribute model through the related schemas
        for schema in self.entity_type.schemas.all():
            if schema.name == attribute_name:
                # Assuming this is the reverse relation to the attribute model
                attribute = schema.attribute_model
                break
        else:
            return  # Attribute not found

        # Create a new value in the Values model
        self.values.create(attribute=attribute,
                           value=value, timestamp=timestamp)

    def delete(self, *args, **kwargs):
        """
        Overrides the delete method to clean up relationships in the Values model.

        When an Entity instance is deleted, this method is called to ensure that
        any references to this Entity in the Values model's 'relationship' 
        field are removed.
        This maintains data integrity by preventing orphaned references.

        It uses a raw SQL query to efficiently remove the Entity's ID from the 
        'relationship' field in all Values instances where it appears.
        """

        # Get the unique identifier of the current Entity instance
        entity_id = self.id

        # Execute a raw SQL query to update the 'relationship' field in the Values model
        # The query removes the Entity's ID from the 'relationship' field
        # in all instances where it is present.
        with connection.cursor() as cursor:
            cursor.execute(f"""
                UPDATE {self._meta.app_label}_{self._meta.object_name.lower()}values
                SET relationship = array_remove(relationship, %s)
                WHERE %s = ANY(relationship);
            """, [entity_id, entity_id])

        # Call the original delete method to complete the deletion of the Entity
        super().delete(*args, **kwargs)


# The ENd
