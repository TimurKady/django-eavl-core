import os
import sys
import pytest
from unittest.mock import patch
import requests
from django.core.exceptions import ValidationError
from django.conf import settings
import django

# Configure Django once
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'django.contrib.admin',
            'treenode',
            'datacore',
        ]
    )
    # Ensure repo root on path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    django.setup()

from datacore.models.schemas import SchemaModel


def test_get_schema_network_failure():
    schema = SchemaModel(pk=1, name='test', title='Test', field_type=21)
    schema.schema = {'$ref': 'http://example.com/schema.json'}
    with patch('datacore.models.schemas.requests.get', side_effect=requests.RequestException('fail')):
        with pytest.raises(ValidationError):
            schema.get_schema()
