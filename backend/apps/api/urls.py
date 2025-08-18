# backend/apps/api/urls.py
from django.urls import path, include

urlpatterns = [
    # This should correctly include the 'v1' folder's urls.py
    path('v1/', include('apps.api.v1.urls')),
]