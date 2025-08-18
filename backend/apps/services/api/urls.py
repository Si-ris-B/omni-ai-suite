# apps/services/api/urls.py
from django.urls import path
from .views import ContainerControlView, ContainerStatusView, ContainerStatusStreamView

urlpatterns = [
    # Endpoint for sending commands (start/stop)
    path('control/', ContainerControlView.as_view(), name='container-control'),

    # Endpoint for checking status of a specific service
    path('<str:service_name>/status/', ContainerStatusView.as_view(), name='container-status'),
# --- ADD THIS NEW URL PATTERN FOR THE STREAMING ENDPOINT ---
    path('<str:service_name>/status-stream/', ContainerStatusStreamView.as_view(), name='container-status-stream'),
]