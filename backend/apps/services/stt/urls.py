# FILE: apps/services/stt/urls.py

from django.urls import path
from .views import (
    TranscribeView, STTStatusView, STTModelControlView, STTProcessView,
    STTModelSettingsView, STTTranscriptionSettingsView
)

app_name = 'stt'

urlpatterns = [
    # Business Logic Endpoints
    path('transcribe/', TranscribeView.as_view(), name='transcribe'),
    path('process/', STTProcessView.as_view(), name='process'),

    # Administrative & Status Endpoints
    path('<str:service_name>/status/', STTStatusView.as_view(), name='status-specific'),

    # Separate load/unload into distinct endpoints for clearer REST semantics
    path('<str:service_name>/model/load/', STTModelControlView.as_view(), {'action': 'load'}, name='model-load'),
    path('<str:service_name>/model/unload/', STTModelControlView.as_view(), {'action': 'unload'}, name='model-unload'),

    # Or keep the single endpoint with action parameter (supports both GET and POST now)
    # path('<str:service_name>/model/<str:action>/', STTModelControlView.as_view(), name='model-control'),

    # Settings Management Endpoints
    path('settings/transcription/', STTTranscriptionSettingsView.as_view(), name='stt-transcription-settings'),
    path('settings/model/<str:service_name>/', STTModelSettingsView.as_view(), name='stt-model-settings'),
    # Add to urls.py:
    # path('debug/srt/', DebugSRTView.as_view(), name='debug-srt'),
]