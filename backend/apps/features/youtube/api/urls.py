from django.urls import path
from .views import YoutubeVideoInfoView, YoutubeTranscribeView

urlpatterns = [
    path('info/', YoutubeVideoInfoView.as_view(), name='youtube-info'),
    path('transcribe/', YoutubeTranscribeView.as_view(), name='youtube-transcribe'),
]