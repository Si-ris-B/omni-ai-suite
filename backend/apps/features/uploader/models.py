# backend/apps/features/uploader/models.py
import os
import uuid
from django.db import models
from django.utils import timezone
from django.utils.text import slugify  # <--- 1. Import slugify
from apps.core.models import TimeStampedModel


def get_upload_path(instance, filename):
    """
    Generates a highly scalable and user-friendly path for uploaded files:
    MEDIA_ROOT/uploads/YYYY/MM/DD/original-filename-shortid.ext

    - Uses the original file's last modified date for the directory structure.
    - Cleans the original filename to make it web-safe.
    - Appends a short unique ID to prevent filename collisions.
    """
    # Use the persistent 'original_modified_at' field. Fall back to now().
    base_date = instance.original_modified_at or timezone.now()

    # --- NEW FILENAME LOGIC ---
    # 1. Get the filename parts
    original_name, ext = os.path.splitext(filename)

    # 2. Clean the original name for web use
    # E.g., "My Resume [final].pdf" -> "my-resume-final"
    slugified_name = slugify(original_name)

    # 3. Generate a short, unique identifier (first 8 chars of a UUID)
    short_id = str(uuid.uuid4())[:8]

    # 4. Combine the parts into a new, unique filename
    # E.g., "my-resume-final-a1b2c3d4.pdf"
    new_filename = f"{slugified_name}-{short_id}{ext}"
    # --- END OF NEW LOGIC ---

    # The path is now based on the original modified date and the new filename
    return os.path.join(
        'uploads',
        base_date.strftime('%Y/%m/%d'),
        new_filename  # <--- Use the new, more descriptive filename
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