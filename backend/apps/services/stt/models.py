# FILE: apps/services/stt/models.py

from django.db import models
from django.core.exceptions import ValidationError
from apps.services.models import ExternalService
from apps.services.stt.languages import LANGUAGE_CHOICES


# --- Base Models ---

class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.pk and self.__class__.objects.exists():
            raise ValidationError(f'Only one instance of {self.__class__.__name__} is allowed.')
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


# --- Settings Models ---

class STTModelSettings(models.Model):
    # ... (This model is correct and remains unchanged)
    service = models.OneToOneField(
        ExternalService,
        on_delete=models.CASCADE,
        limit_choices_to={'service_type': 'stt'},
        help_text="The STT service this configuration applies to."
    )
    model_size_or_path = models.CharField(max_length=255, default="base",
                                          help_text="Model name (e.g., 'base.en'), HuggingFace ID, or path.")
    device = models.CharField(max_length=20, default="auto",
                              choices=[("auto", "Auto"), ("cuda", "CUDA (GPU)"), ("cpu", "CPU")])
    compute_type = models.CharField(max_length=20, default="default",
                                    choices=[("default", "Default"), ("auto", "Auto"), ("int8", "int8"),
                                             ("int8_float16", "int8_float16"), ("float16", "float16"),
                                             ("float32", "float32")])
    device_index = models.CharField(max_length=50, default="0",
                                    help_text="GPU device index/indices (e.g., '0' for one GPU, '0,1' for two).")
    cpu_threads = models.PositiveIntegerField(default=0,
                                              help_text="Number of CPU threads to use (0 for auto-detection).")
    num_workers = models.PositiveIntegerField(default=1,
                                              help_text="Number of workers for loading the model (higher can be faster on multi-core CPUs).")

    def __str__(self):
        try:
            return f"Settings for {self.service.display_name}"
        except ExternalService.DoesNotExist:
            return "Orphaned STT Settings"

    class Meta:
        verbose_name = "STT Model Setting"
        verbose_name_plural = "STT Model Settings"


class STTTranscriptionSettings(SingletonModel):
    language = models.CharField(max_length=10, blank=True, null=True, choices=LANGUAGE_CHOICES,
                                help_text="Language code (e.g., 'en'). Blank for auto-detect.")
    task = models.CharField(max_length=20, default="transcribe",
                            choices=[("transcribe", "Transcribe"), ("translate", "Translate to English")])
    word_timestamps = models.BooleanField(default=False, help_text="Enable word-level timestamps.")
    beam_size = models.PositiveIntegerField(default=5)
    best_of = models.PositiveIntegerField(default=5)
    patience = models.FloatField(default=1.0)
    length_penalty = models.FloatField(default=1.0)

    # --- THIS IS THE FIX ---
    # Changed from CharField to FloatField to support a slider UI.
    temperature = models.FloatField(
        default=0.0,
        help_text="Temperature for sampling. Higher values make the output more random. (0.0 to 1.0)"
    )
    # --- END FIX ---

    compression_ratio_threshold = models.FloatField(default=2.4, blank=True, null=True)
    log_prob_threshold = models.FloatField(default=-1.0, blank=True, null=True)
    no_speech_threshold = models.FloatField(default=0.6, blank=True, null=True)
    vad_filter = models.BooleanField(default=False,
                                     help_text="Enable Voice Activity Detection (VAD) to filter out non-speech.")
    condition_on_previous_text = models.BooleanField(default=True,
                                                     help_text="Condition the model on the previous text segment.")
    initial_prompt = models.TextField(blank=True, null=True, help_text="Optional text to provide as a prompt.")
    repetition_penalty = models.FloatField(default=1.0)
    no_repeat_ngram_size = models.PositiveIntegerField(default=0)

    def __str__(self):
        return "STT Default Transcription Parameters"

    class Meta:
        verbose_name = "STT Transcription Setting"
        verbose_name_plural = "STT Transcription Settings"