import uuid
from django.db import models

class ExternalService(models.Model):
    """
    A central registry for all external microservices the platform connects to.
    This model uses a UUID as its primary key for robust, decoupled relationships.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    SERVICE_TYPE_CHOICES = [
        ('stt', 'Speech-to-Text'),
        ('tts', 'Text-to-Speech'),
        ('llm', 'Large Language Model'),
        ('other', 'Other'),
    ]

    machine_name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="A unique, machine-readable name for the service (e.g., 'stt_whisper'). This cannot be changed after creation."
    )

    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    service_type = models.CharField(max_length=10, choices=SERVICE_TYPE_CHOICES, default='other')

    service_url = models.URLField(help_text="The base URL of the external service (e.g., http://localhost:8088).")

    container_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The exact name or ID of the running Docker container to be controlled (e.g., 'faster_whisper_stt_service_container')."
    )

    is_enabled = models.BooleanField(default=True, help_text="Enable or disable usage of this service.")

    is_default = models.BooleanField(
        default=False,
        help_text="Set to True for this to be the default service of its type (e.g., the default STT)."
    )

    class Meta:
        ordering = ['display_name']
        verbose_name = "External Service"
        verbose_name_plural = "External Services"
        constraints = [
            models.UniqueConstraint(fields=['service_type', 'is_default'], condition=models.Q(is_default=True), name='unique_default_per_service_type')
        ]

    def __str__(self):
        return self.display_name