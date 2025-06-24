# -*- coding: utf-8 -*-
"""
Forms Module.

Version: 0.0.1
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django import forms


class DynamicEntityForm(forms.ModelForm):
    """Dynamic Entity Form."""

    class Meta:
        """Form Meta class."""

        model = None
        fields = []

    def __init__(self, *args, **kwargs):
        """Init form."""
        entity_class = kwargs.pop("entity_class", None)
        super().__init__(*args, **kwargs)

        if entity_class is None:
            raise ValueError(
                "entity_class is required to build dynamic fields"
            )

        for attr in entity_class.attributes.all():
            schema = attr.schema.to_dict()
            field_type = schema.get("type")
            self.fields[attr.code] = self._build_field(
                attr.code, field_type, schema)

    def _build_field(self, name, field_type, schema):
        """Build field."""
        if field_type == "string":
            return forms.CharField(
                label=schema.get("title"),
                required=False,
                initial=schema.get("default")
            )
        elif field_type == "integer":
            return forms.IntegerField(
                label=schema.get("title"),
                required=False,
                initial=schema.get("default")
            )
        elif field_type == "boolean":
            return forms.BooleanField(
                label=schema.get("title"),
                required=False,
                initial=schema.get("default")
            )
        elif field_type == "array":
            return forms.CharField(
                label=schema.get("title"),
                required=False,
                help_text="Comma-separated list"
            )
        else:
            return forms.CharField(label=name, required=False)


# The End
