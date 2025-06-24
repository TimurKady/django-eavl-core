from django import forms
from django.test import SimpleTestCase
from django.conf import settings
import django

from datacore.forms import DynamicEntityForm

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
        ],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        USE_TZ=True,
        SECRET_KEY='test',
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
    )
    django.setup()


class DummySchema:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


class DummyAttr:
    def __init__(self, code, schema):
        self.code = code
        self.schema = DummySchema(schema)


class AttrList(list):
    def all(self):
        return self


class DummyEntityClass:
    def __init__(self, attrs):
        self.attributes = AttrList(attrs)


from django.db import models


class DummyModel(models.Model):
    class Meta:
        app_label = 'tests'


class DummyForm(DynamicEntityForm):
    class Meta:
        model = DummyModel
        fields = []


class DynamicFormTests(SimpleTestCase):
    def test_dynamic_fields_created_from_schema(self):
        attrs = [
            DummyAttr("first", {"type": "string", "title": "First"}),
            DummyAttr("age", {"type": "integer", "title": "Age"}),
        ]
        entity_class = DummyEntityClass(attrs)
        form = DummyForm(entity_class=entity_class)
        self.assertIn("first", form.fields)
        self.assertIsInstance(form.fields["first"], forms.CharField)
        self.assertEqual(form.fields["first"].label, "First")
        self.assertIn("age", form.fields)
        self.assertIsInstance(form.fields["age"], forms.IntegerField)
        self.assertEqual(form.fields["age"].label, "Age")

