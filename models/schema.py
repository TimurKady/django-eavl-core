# -*- coding: utf-8 -*-

"""
Data Schema with Validation

Description:
This module defines Django models for managing data schemas and their 
associated validators. It allows users to create, customize, and validate 
data schemas with various field types and validation rules. Schemas can be 
organized as a tree structure, and each schema can have multiple associated 
validators with configurable parameters.

Models:
- Schema: Represents a data schema with attributes like name, title, 
description, field type, validators, and more.
- Validator: Represents a validator associated with a schema, specifying the 
validation type and parameters.

Dependencies:
- Django: The web framework for building web applications using Python.
- Marshmallow: A popular library for object serialization/deserialization.
- TreeNode: A Django package for hierarchical data structures.

Usage:
1. Define data schemas with customizable field types and validation rules.
2. Organize schemas as a tree structure using TreeNodeModel.
3. Create and manage validators for each schema with specific validation parameters.
4. Validate data against schemas with associated validators.

This module provides a flexible and extensible way to manage and validate data 
schemas in Django applications.

Author: Timur Kady
Created on: Dec 15 2023
"""

# Rest of your code here...


from django.db import models
from treenode.models import TreeNodeModel
from .constants import FIELD_TYPES, VALIDATOR_TYPES, UNIQUE_SET
from marshmallow import Schema as MarshmallowSchema, fields as MarshmallowFields
from marshmallow import validate
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _


class Schema(TreeNodeModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_('Internal name'),
        help_text=_(
            'Program scheme name. Less than 32 characters without spaces.'),
    )

    title = models.CharField(
        max_length=254,
        unique=True,
        verbose_name=_('Title'),
        help_text=_('Display title. Used for display in forms.'),
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Describe the purpose of the field.'),
    )

    field_type = models.IntegerField(
        choices=FIELD_TYPES,
        verbose_name=_('Field type'),
        help_text=_(
            'Specify the type of data that can be stored in the field.'),
    )

    unique_set = models.IntegerField(
        choices=UNIQUE_SET,
        default=UNIQUE_SET.normal,
        verbose_name=_('Is it unique?'),
        help_text=_(
            'Specify the mode for checking the uniqueness of input values.'),
    )

    is_time_series: models.BooleanField(
        default=False,
        verbose_name=_('Is it a time series?'),
        help_text=_('Specify whether data changes should be stored in this \
field.'),
    )

    class Meta:
        verbose_name = 'Data Schema'
        verbose_name_plural = 'Data Schemas'

    def __str__(self):
        return self.name

    def get_marshmallow_field_type(self):
        """
        Get the corresponding Marshmallow field type based on the field_type 
        attribute.

        :return: Marshmallow field type instance.
        """
        if self.is_root():
            field_type_mapping = {
                0: MarshmallowFields.Nested,
                1: MarshmallowFields.Boolean,
                2: MarshmallowFields.Constant,
                3: MarshmallowFields.Date,
                4: MarshmallowFields.DateTime,
                5: MarshmallowFields.Decimal,
                6: MarshmallowFields.Email,
                7: MarshmallowFields.Enum,
                8: MarshmallowFields.Float,
                9: MarshmallowFields.IP,
                10: MarshmallowFields.Integer,
                11: MarshmallowFields.Raw,
                12: MarshmallowFields.String,
                13: MarshmallowFields.String,
                14: MarshmallowFields.Time,
                15: MarshmallowFields.TimeDelta,
                16: MarshmallowFields.URL,
                17: MarshmallowFields.UUID,
            }

            marshmallow_field_type = field_type_mapping.get(self.field_type)

            if marshmallow_field_type is None:
                raise ValueError("Invalid field_type value")

            if self.field_type == 0:
                return marshmallow_field_type(self)
            else:
                return marshmallow_field_type()
        else:
            raise ValueError(
                "This method can only be called on the root schema.")

    def get_schema(self):
        """
        Get a Marshmallow schema representation of the current schema.

        :return: Marshmallow schema instance.
        """
        if self.is_root():
            schema = MarshmallowSchema()
            schema.fields = {
                'name': MarshmallowFields.Str(),
                'description': MarshmallowFields.Str(),
                'field_type': self.get_marshmallow_field_type(),
                'validator_type': MarshmallowFields.Integer(allow_none=True),
                'validator_params': MarshmallowFields.Dict(allow_none=True),
                'unique_set': MarshmallowFields.Integer(),
                'is_time_series': MarshmallowFields.Boolean(),
            }
            return schema
        else:
            raise ValueError(
                "This method can only be called on the root schema.")

    def get_schema_dict(self):
        """
        Get a dictionary representation of the current schema.

        :return: Dictionary containing schema data.
        """
        if self.is_root():
            schema_dict = {
                'name': self.name,
                'description': self.description,
                'field_type': self.field_type,
                'validator_type': self.validator_type,
                'validator_params': self.validator_params,
                'unique_set': self.unique_set,
                'is_time_series': self.is_time_series,
            }
            return schema_dict
        else:
            raise ValueError(
                "This method can only be called on the root schema.")

    def validate_data(self, data):
        """
        Validate input data against the schema using specified validators.

        :param data: Data to be validated.
        :return: List of validation errors or an empty list if data is valid.
        """
        schema = self.get_schema()

        validator_mapping = {
            0: validate.Equal,
            1: validate.Length,
            2: validate.OneOf,
            3: validate.Range,
            4: validate.Regexp,
            # Add other validators here as needed
        }

        validator_instances = []
        for validator_info in self.validators.all():
            validator_class = validator_mapping.get(validator_info.type)

            if validator_class is None:
                raise ValueError(f"Invalid validator_type value for {
                                 validator_info}")

            validator = validator_class(**validator_info.params)
            validator_instances.append(validator)

        combined_validator = validate.OneOf(validator_instances)

        errors = schema.validate(data, validator=combined_validator)

        if errors:
            return errors
        else:
            return []


class Validator(models.Model):
    schema = models.ForeignKey(
        Schema,
        on_delete=models.CASCADE,
        related_name='validators',
        verbose_name=_('Schema'),
        help_text=_('The schema this validator belongs to.'),
    )

    type = models.IntegerField(
        choices=VALIDATOR_TYPES,
        verbose_name=_('Validator type'),
        help_text=_('Specify the type of validator for data verification.'),
    )

    params = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        verbose_name=_('Validator parameters'),
        help_text=_('Specify parameters for the validator.'),
    )

    class Meta:
        verbose_name = 'Validator'
        verbose_name_plural = 'Validators'

    def __str__(self):
        return f"{self.get_type_display()} Validator for {self.schema}"
