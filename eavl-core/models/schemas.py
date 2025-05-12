# -*- coding: utf-8 -*-
"""
Data schema module.

This module implements minimal support for attribute data schemas. It is
intended to be used by default. Provides a minimal set of functionality.

In real projects, the schema model should be overridden, for example, by
a specialized application django-schema-core, by setting the global variable
`eavl_schemas`

Version: 0.0.1
Author: Timur Kady
Email: timurkady@yandex.com
"""

import requests
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _
from marshmallow import Schema


class SchemaModel(models.Model):
    """SchemaModel class."""

    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        verbose_name=_('schema name'),
    )

    schema = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('schema'),
        encoder=DjangoJSONEncoder,
    )

    version = models.CharField(
        max_length=20,
        default="1.0"
    )

    class Meta:
        """Meta options for SchemaModel."""

        ordering = ["name"]

    def __str__(self):
        """Return a readable representation of the attribute."""
        return self.name

    def get_schema(self):
        """Return marshmellow schema."""
        schema_dict = self.schema
        if "$ref" in schema_dict:
            url = schema_dict["$ref"]
            schema_dict = requests.get(url).json()

        return Schema.from_dict(schema_dict)

    def to_dict(self):
        """Return schema as dict."""
        return self.schema

    def get_defaults(self):
        """Return defaults values."""
        return self.schema.get("default", None)


eavl_schemas = SchemaModel
