# -*- coding: utf-8 -*-
"""
Admin Module.

Version: 0.0.1
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.contrib import admin
from treenode.admin import TreeNodeModelAdmin
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import urlencode

from .models.schemas import eavl_schemas


# === Main admin for entity classes ===


class ValueAdminModel(admin.ModelAdmin):
    """Admin class for AbstractValueModel."""

    pass


class AttributeAdminModel(admin.ModelAdmin):
    """Admin class for AbstractAttributeModel."""

    pass


class EntityAdminModel(admin.ModelAdmin):
    """Admin class for AbstractEntityModel."""

    list_display = ("id", "entity_class",)
    search_fields = ("title",)
    # change_list_template = "admin/entity_changelist.html"

    class Media:
        """Meta Class."""

        css = {"all": (
            # "css/entity_admin.css",
        )}
        js = (
            # "js/entity_admin.js",
        )


class EntityClassAdminModel(TreeNodeModelAdmin):
    """Base EntityClassModel Admin class."""

    list_display = ("title",)
    search_fields = ("title",)

    def __init__(self, model, admin_site):
        """Init admin model."""
        super().__init__(model, admin_site)

# === Dinamic Admin ===


# === Admin panel for schemes ===


@admin.register(eavl_schemas)
class SchemaModelAdmin(admin.ModelAdmin):
    """SchemaModel Admin class."""

    list_display = ["title", "version"]
    fieldsets = [
        (
            None, {
                "fields": [
                    ("title", "name",), "version",
                    ("field_type", "is_multiple",),
                ],
            }
        )
    ]
    prepopulated_fields = {"name": ["title"]}
    search_fields = ["title", "name"]
    show_full_result_count = 20
