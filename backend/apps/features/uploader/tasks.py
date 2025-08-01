from celery import shared_task
from django.utils import timezone
from .models import UploadedFile
import logging

logger = logging.getLogger(__name__)

@shared_task
def delete_expired_uploaded_files():
    """
    Finds and deletes all UploadedFile objects that have passed their expiration date.
    """
    now = timezone.now()
    # Find files where expires_at is not null and is in the past
    expired_files = UploadedFile.objects.filter(expires_at__isnull=False, expires_at__lte=now)
    count = expired_files.count()

    if count > 0:
        logger.info(f"Found {count} expired uploaded files to delete.")
        for uploaded_file in expired_files:
            try:
                # This deletes the file from storage (local disk, S3, etc.)
                uploaded_file.file.delete(save=False)
                # This deletes the record from the database
                uploaded_file.delete()
                logger.info(f"Deleted file: {uploaded_file.file.name}")
            except Exception as e:
                logger.error(f"Error deleting file {uploaded_file.pk}: {e}")
    else:
        logger.info("No expired uploaded files to delete.")

    return f"Completed cleanup. Deleted {count} files."