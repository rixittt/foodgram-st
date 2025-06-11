from django.apps import AppConfig


class CustomAPIConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
