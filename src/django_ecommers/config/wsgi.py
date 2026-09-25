"""
WSGI config for django_ecommers project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

import dotenv
from django.core.wsgi import get_wsgi_application

dotenv.load_dotenv()

os.environ.get("DJANGO_SETTINGS_MODULE", "django_ecommers.settings")

application = get_wsgi_application()
