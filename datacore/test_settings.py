SECRET_KEY='test'
INSTALLED_APPS=[
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.admin',
    'treenode',
    'datacore',
]
DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}
MIDDLEWARE=[]
USE_TZ=True
DEBUG=False
