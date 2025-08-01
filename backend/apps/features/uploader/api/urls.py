# backend/apps/features/uploader/api/urls.py
from django.urls import path
from .views import FileUploadView

urlpatterns = [
    # The final part of the path is 'upload/'. The full path is built by the includes.
    path('upload/', FileUploadView.as_view(), name='file-upload'),
]