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
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _
from functools import lru_cache
from marshmallow import Schema, fields as mf


class MarshmallowField(models.PositiveSmallIntegerField):
    """A Django model field that maps integers to marshmallow field classes."""

    registry = [
        (2, _("Boolean"), _("A boolean field"), mf.Boolean),
        (4, _("Date"), _("Date field"), mf.Date),
        (5, _("DateTime"), _("Datetime field"), mf.DateTime),
        (6, _("Decimal"), _("Decimal number"), mf.Decimal),
        (7, _("Dict"), _("Dictionary field"), mf.Dict),
        (8, _("Email"), _("Email address"), mf.Email),
        (9, _("Enum"), _("Enumeration"), mf.Enum),
        (10, _("Float"), _("Floating-point number"), mf.Float),
        (12, _("Int"), _("Alias of Integer"), mf.Int),
        (13, _("Integer"), _("Integer number"), mf.Integer),
        (14, _("IP"), _("IP address"), mf.IP),
        (15, _("IPInterface"), _("IP network interface"), mf.IPInterface),
        (17, _("Mapping"), _("Key-value pairs (typed dict)"), mf.Mapping),
        (21, _("String"), _("String field"), mf.String),
        (22, _("Time"), _("Time field"), mf.Time),
        (23, _("TimeDelta"), _("Time difference"), mf.TimeDelta),
        (25, _("URL"), _("URL string"), mf.URL),
        (26, _("UUID"), _("UUID value"), mf.UUID),
    ]

    def __init__(self, *args, **kwargs):
        """Init instance."""
        # Превращаем registry в список choices
        choices = [(entry[0], entry[1]) for entry in self.registry]
        kwargs['choices'] = choices
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        """Serialize choices."""
        name, path, args, kwargs = super().deconstruct()
        # Django сам сериализует choices, если они явно переданы
        return name, path, args, kwargs

    @classmethod
    def get_field_name(cls, value):
        """Return the marshmallow field name by int-code."""
        field_class = cls.get_field_class(value)
        return field_class.__name__.lower() if field_class else None

    @classmethod
    def get_field_class(cls, value):
        """Return the marshmallow field by int-code."""
        for item in cls.registry:
            if item[0] == value:
                return item[3]
        return None


class SchemaModel(models.Model):
    """SchemaModel class."""

    title = models.CharField(
        max_length=255,
        unique=True,
        null=False,
        blank=False,
        verbose_name=_('schema/attribute title'),
    )

    name = models.SlugField(
        max_length=32,
        unique=True,
        null=False,
        blank=False,
        verbose_name=_('schema name'),
        help_text=_("Internal short label for schema,\
containing only letters, numbers, underscores or hyphens"),
    )

    version = models.CharField(
        max_length=20,
        default="1.0"
    )

    field_type = MarshmallowField(
        null=False,
        blank=False,
        verbose_name=_('Field type')
    )

    is_multiple = models.BooleanField(
        default=False,
        verbose_name=_('is multiple'),
        help_text=_('If True, values are treated as a list.')
    )

    schema = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('schema'),
        encoder=DjangoJSONEncoder,
        editable=False,
    )

    class Meta:
        """Meta options for SchemaModel."""

        ordering = ["name"]
        unique_together = [["name", "version"]]
        verbose_name = _("\u200AData scema")
        verbose_name_plural = _("\u200AData schemas")

    def __str__(self):
        """Return a readable representation of the attribute."""
        return f"{self.name} ({self.version})"

    @lru_cache(maxsize=128)
    def get_schema(self):
        """Return marshmallow schema."""
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
        super().delete

    def delete(self):
        """Delete schema instance."""
        if self.classes.exists():
            raise ValidationError(
                "Cannot delete schema with linked entity classes.")
        super().delete()

    def get_next_version(self):
        """Get next ctean verion."""
        name = self.name
        current = self.version
        major, minor = map(int, current.split('.'))

        while True:
            minor += 1
            candidate = f"{major}.{minor}"
            if not SchemaModel.objects.filter(name=name, version=candidate).exists():  # noqa: D501
                return candidate

    def clean(self):
        """Validate instance."""
        if self.field_type is None:
            raise ValidationError(
                {"field_type": _("Field type is required.")}
            )

        if not self.name.replace('-', '').replace('_', '').isalnum():
            raise ValidationError(
                {"name": _("Schema name must be a valid slug.")}
            )

    def clone(self):
        """Clone current instance without links."""
        # Copy all fields except ID
        fields = models.model_to_dict(self, exclude=['id'])

        # Increment a minor version (eg 1.3 -> 1.4)
        fields["version"] = self.get_next_version()

        # Rebuild schema manually, since model_to_dict ignores JSONField
        # with editable=False
        fields["schema"] = self.schema

        # Create a new instance without connections
        return self._meta.model.objects.create(**fields)

    def save(self, force_insert=False, *args, **kwargs):
        """Save schema instance.

        If instance is linked (via `classes`), don't update it.
        Instead, create a new version (without links).
        """
        # === Generate JSON Schema ===
        field_type_name = MarshmallowField.get_field_name(self.field_type)
        if field_type_name is None:
            raise ValueError(f"Unknown field type: {self.field_type}")

        if self.is_multiple:
            schema_dict = {
                "type": "array",
                "items": {
                    "type": field_type_name,
                }
            }
        else:
            schema_dict = {
                "type": field_type_name,
            }

        self.schema = schema_dict

        # === Versioning ===
        if self.pk and self.classes.exists():
            self.clone()
            return

        # Normal save
        self.full_clean()
        super().save(force_insert=force_insert, *args, **kwargs)


eavl_schemas = SchemaModel
