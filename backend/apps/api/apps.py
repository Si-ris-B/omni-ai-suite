# backend/apps/api/apps.py

from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # This 'name' MUST match what you put in INSTALLED_APPS in settings.py
    name = 'apps.api' 