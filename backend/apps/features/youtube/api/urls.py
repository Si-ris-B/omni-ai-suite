from django.urls import path
from .views import YoutubeVideoInfoView, YoutubeTranscribeView, YoutubePrepareAudioView # Add new import

urlpatterns = [
    path('info/', YoutubeVideoInfoView.as_view(), name='youtube-info'),
    path('transcribe/', YoutubeTranscribeView.as_view(), name='youtube-transcribe'),
    # --- ADD THIS NEW ENDPOINT ---
    # This endpoint takes a URL, downloads the audio, creates an UploadedFile,
    # and returns its details.
    path('prepare/', YoutubePrepareAudioView.as_view(), name='youtube-prepare'),
]