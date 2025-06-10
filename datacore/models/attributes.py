# -*- coding: utf-8 -*-
"""
Abstract Attribute Model

This model defines the base structure for attributes in an EAVL architecture.

Each attribute describes a piece of data attached to an entity.
Attributes can be typed, single or multiple, time-based (timeseries), or act as
relations (linking one entity to another). Schemas define their expected
 structure and validation rules.

Version: 0.0.1
Author: Timur Kady
Email: timurkady@yandex.com
"""

from datetime import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _

from .schemas import eavl_schemas


class AbstractAttributeModel(models.Model):
    """Abstract base model for describing an entity attribute."""

    entity = models.BigIntegerField()

    title = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        verbose_name=_('attribute name'),
    )

    code = models.SlugField(
        null=False,
        blank=False,
        db_index=True,
        verbose_name=_('code'),
        help_text=_('Internal code/name of the attribute. ' \
           'Allowed characters: letters, digits, underscores and ' \
           'hyphens; must start with a letter or underscore.'),
    )

    schema = models.ForeignKey(
        eavl_schemas,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="attributes",
        verbose_name=_('schema'),
        help_text=_('Used attribute data schema'),
    )

    is_multiple = models.BooleanField(
        default=False,
        verbose_name=_('is multiple'),
        help_text=_('If True, values are treated as a list.')
    )

    is_relation = models.BooleanField(
        default=False,
        verbose_name=_('is a link'),
        db_index=True,
        help_text=_(
            'If True, values are treated as references to another entity.')
    )

    destination = models.BigIntegerField()

    is_timeseries = models.BooleanField(
        default=False,
        verbose_name=_('is a time series'),
        help_text=_('If True, values are stored with timestamps and ordered chronologically.')  # noqa: D501
    )

    deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        """Meta options for abstract attribute model."""

        abstract = True
        ordering = ["title"]
        unique_together = [["entity", "code"]]
        indexes = [
            models.Index(fields=["entity", "id"]),
        ]

    def __str__(self):
        """Return a readable representation of the attribute."""
        return f"{self.title} ({self.code})"

    def to_dict(self, include_values=True):
        """
        Serialize attribute structure as a dictionary.

        Optionally include values, fetched through get_value().
        """
        result = {
            "title": self.title,
            "code": self.code,
            "schema": self.schema.to_dict(),
            "is_multiple": self.is_multiple,
        }

        if self.is_relation:
            result.update({
                "is_relation": True,
                "destination": self.destination,
            })

        if include_values:
            result.update({
                "values": self.get_value(),
            })

        return result

    def get_value(self, last_only=True, from_date=None, to_date=None):
        """
        Retrieve attribute value(s) for the current entity.

        Handles polymorphism: single, multiple, timeseries.

        Params:
        - last_only: Return only the latest value (for time series or
          multi-value attributes).
        - from_date: If set, limits time series to values from this datetime.
        - to_date: If set, limits time series to values before this datetime.

        Returns:
        - dict with attribute code as key and value(s) or list of values.
        """
        data = {}
        values_qs = self.values.filter(
            entity=self.entity).order_by("-timestamp")

        if self.is_timeseries:
            if not last_only:
                options = {}
                if from_date:
                    options["timestamp__gte"] = from_date
                if to_date:
                    options["timestamp__lte"] = to_date
                if options:
                    values_qs = values_qs.filter(**options)

                data[self.code] = [
                    {"value": v.value, "timestamp": v.timestamp.isoformat()}
                    for v in values_qs
                ]
            else:
                value = values_qs.first()
                if value:
                    data[self.code] = {
                        "value": value.value,
                        "timestamp": value.timestamp.isoformat()
                    }
                else:
                    data[self.code] = None

        elif self.is_multiple:
            if last_only:
                value = values_qs.first()
                data[self.code] = value.value if value else None
            else:
                data[self.code] = [v.value for v in values_qs]

        else:
            value = values_qs.first()
            data[self.code] = value.value if value else None

        return data

    def get_schema(self):
        """Return marshmallow schema."""
        return self.schema.get_schema()

    def set_value(self, value: any) -> None:
        """
        Set value(s) for this attribute.

        Supports setting:
        - single value (default)
        - multiple values
        - time series values: list of (value, timestamp) tuples
        """
        value_model = self.values.model
        values_qs = value_model.objects.\
            filter(entity=self.entity, deleted=False)\
            .order_by("-timestamp")
        default = self.schema.get_defaults()
        created = False

        # Handle time series: bulk insert list of (value, timestamp)
        if self.is_timeseries and isinstance(value, list):
            objs = []
            for item in value:
                val, ts = item
                if ts and ts < datetime.now():
                    objs.append(value_model(
                        value=val if val is not None else default,
                        entity=self.entity,
                        attribute=self,
                        timestamp=ts
                    ))
            if objs:
                return value_model.objects.bulk_create(objs, batch_size=2000)

        # Single value or multiple (last_only)
        obj = values_qs.first()
        if obj:
            obj.value = value
        else:
            obj = value_model(
                value=value,
                entity=self.entity,
                attribute=self
            )
            created = True
        obj.save()

        return obj, created

    def delete(self):
        """Lazzy delete instance."""
        self.deleted = True
        self.save()

    def save(self, *args, **kwargs):
        """Save instance."""
        if self.is_relation and self.destination is None:
            raise AttributeError(
                "The `destination` field must be specified for link-attributes."
            )
        super().save(*args, **kwargs)

# The End
