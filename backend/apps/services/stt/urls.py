from django.urls import path
from .views import TranscribeView, STTStatusView, STTModelControlView, STTProcessView

app_name = 'stt'

urlpatterns = [
    # This endpoint is specifically for transcribing an already uploaded file by its ID.
    path('transcribe/', TranscribeView.as_view(), name='transcribe'),

    # This is the new, unified endpoint for starting a transcription job
    # from either a file upload or a YouTube URL.
    path('process/', STTProcessView.as_view(), name='process'),

    # --- Administrative / Debug Endpoints ---
    # These endpoints allow an admin to interact with specific services.

    # Get status of the default STT service
    path('status/', STTStatusView.as_view(), name='status-default'),
    # Get status of a specific STT service by its machine_name
    path('<str:service_name>/status/', STTStatusView.as_view(), name='status-specific'),

    # Send a command to a specific STT service by its machine_name
    path('<str:service_name>/model/<str:action>/', STTModelControlView.as_view(), name='model-control'),
]