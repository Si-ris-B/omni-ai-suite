from django.contrib import admin
from .models import STTTranscriptionSettings

@admin.register(STTTranscriptionSettings)
class STTTranscriptionSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Core Parameters", {'fields': ('language', 'task', 'word_timestamps')}),
        ("Beam Search & Sampling", {
            'description': "Controls the quality and diversity of the output.",
            'classes': ('collapse',),
            'fields': ('beam_size', 'best_of', 'patience', 'length_penalty', 'temperature', 'repetition_penalty', 'no_repeat_ngram_size')
        }),
        ("Thresholds & Filtering", {
            'description': "Fine-tune what the model considers valid speech.",
            'classes': ('collapse',),
            'fields': ('compression_ratio_threshold', 'log_prob_threshold', 'no_speech_threshold', 'vad_filter')
        }),
        ("Advanced Control", {
            'description': "Provide context or prompts to the model.",
            'classes': ('collapse',),
            'fields': ('condition_on_previous_text', 'initial_prompt')
        }),
    )

    def has_add_permission(self, request):
        return not STTTranscriptionSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False