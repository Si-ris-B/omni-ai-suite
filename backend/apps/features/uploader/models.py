# backend/apps/features/uploader/models.py
import os
import uuid
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


def get_upload_path(instance, filename):
    """
    Generates a highly scalable path for uploaded files:
    MEDIA_ROOT/uploads/YYYY/MM/DD/uuid.ext

    This function now relies on the persistent 'original_modified_at' field
    of the model instance.
    """
    # Use the persistent 'original_modified_at' field. Fall back to now()
    # if it's somehow not set when this function is called.
    base_date = instance.original_modified_at or timezone.now()

    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"

    # The path is now based on the original modified date
    return os.path.join(
        'uploads',
        base_date.strftime('%Y/%m/%d'),
        unique_filename
    )


class UploadedFile(TimeStampedModel):
    """
    Represents a file uploaded by a user.
    The folder structure is determined by the file's original last modified date.
    """
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
    ]

    # The actual file, saved using our custom path function
    file = models.FileField(upload_to=get_upload_path)

    # We store the original filename separately for user display purposes
    original_filename = models.CharField(max_length=255)

    # The file type provided by the frontend
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)

    # New field to store the original 'last modified' date for our records
    original_modified_at = models.DateTimeField(
        default=timezone.now,
        help_text="The last modified timestamp of the original file."
    )

    def __str__(self):
        return self.original_filename