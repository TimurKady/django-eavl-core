# -*- coding: utf-8 -*-
"""


Version: 0.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DatacoreConfig(AppConfig):
    """App congig class."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "datacore"
    verbose_name = _("EAVL Core")

    def ready(self):
        """App ready."""
        from django.apps import apps
        from django.contrib import admin
        from .models import AbstractEntityClassModel
        from .admin import (
            EntityAdminModel, AttributeAdminModel, ValueAdminModel,
        )

        for model in apps.get_models():
            if not issubclass(model, AbstractEntityClassModel):
                continue
            if model._meta.abstract or model._meta.proxy:
                continue

            # Trigger __init_subclass__() (if it wasn't called)
            if not all(hasattr(model, a) for a in (
                    "entity_model", "attr_model", "value_model")):
                model.__init_subclass__()

            # Then register entity, attributes and values
            for related, admin_class in zip(
                [model.entity_model, model.attr_model, model.value_model],
                [EntityAdminModel, AttributeAdminModel, ValueAdminModel]
            ):
                if related and not admin.site.is_registered(related):
                    try:
                        admin.site.register(related, admin_class)
                    except admin.sites.AlreadyRegistered:
                        pass
