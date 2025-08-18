# backend/apps/api/v1/urls.py
from django.urls import path, include

urlpatterns = [
    # Make sure this path is correct and there are no stray characters.
    # It should be a string: 'apps.features.uploader.api.urls'
    path('uploader/', include('apps.features.uploader.api.urls')),

    # ... include other apps here
    # Include the generic container management API URLs
    path('containers/', include('apps.services.api.urls')),
    path('stt/', include('apps.services.stt.urls', namespace='stt')),
    path('youtube/', include('apps.features.youtube.api.urls')),
]