from django.apps import AppConfig

class YoutubeApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.features.youtube.api'
    label = 'youtube_api'  # Unique label to avoid conflicts