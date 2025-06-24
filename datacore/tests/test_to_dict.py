import types
from django.conf import settings
import django

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.admin', 'django.contrib.contenttypes', 'datacore'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
    django.setup()

from datacore.models.entity import AbstractEntityModel

class FakeAttr:
    def __init__(self, code, schema, is_relation=False, deleted=False):
        self.code = code
        self.schema = schema
        self.is_relation = is_relation
        self.deleted = deleted
    def to_dict(self, include_values=True):
        return {'code': self.code}

class FakeManager:
    def __init__(self, attrs):
        self._attrs = attrs
    def filter(self, **kwargs):
        result = []
        for attr in self._attrs:
            if 'is_relation' in kwargs and attr.is_relation != kwargs['is_relation']:
                continue
            if 'deleted' in kwargs and attr.deleted != kwargs['deleted']:
                continue
            if 'schema__in' in kwargs and attr.schema not in kwargs['schema__in']:
                continue
            result.append(attr)
        return result

class FakeSchema:
    pass

class FakeClass:
    def __init__(self, schemas, ancestors=None):
        self.schemas = types.SimpleNamespace(all=lambda: schemas)
        self._ancestors = ancestors or []
    def get_ancestors(self, include_self=True):
        res = list(self._ancestors)
        if include_self:
            res.append(self)
        return res

class FakeEntity(AbstractEntityModel):
    class Meta:
        abstract = True

    def __init__(self, entity_class, attrs):
        self.entity_class = entity_class
        self.attributes = FakeManager(attrs)
        self.entity_class_id = 1
        self.title = 'Entity'
        self.uuid = 'uid'


def test_to_dict_includes_inherited_attrs():
    parent_schema = FakeSchema()
    child_schema = FakeSchema()
    parent_class = FakeClass([parent_schema])
    child_class = FakeClass([child_schema], ancestors=[parent_class])

    attrs = [
        FakeAttr('parent_attr', parent_schema),
        FakeAttr('child_attr', child_schema),
    ]
    entity = FakeEntity(child_class, attrs)

    result = entity.to_dict()
    codes = {p['code'] for p in result['properties']}
    assert 'parent_attr' in codes
    assert 'child_attr' in codes
