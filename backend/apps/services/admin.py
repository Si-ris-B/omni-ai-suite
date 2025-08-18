from django.contrib import admin
from .models import ExternalService
from apps.services.stt.models import STTModelSettings

# Explicitly import the admin configurations from the 'stt' submodule.
import apps.services.stt.admin

class STTModelSettingsInline(admin.StackedInline):
    model = STTModelSettings
    can_delete = False
    verbose_name_plural = 'STT Model Configuration'
    fieldsets = (
        ("Model Selection", {'fields': ('model_size_or_path',)}),
        ("Hardware & Performance Configuration", {
            'description': "Configure how the model utilizes hardware resources.",
            'fields': ('device', 'compute_type', 'device_index', 'cpu_threads', 'num_workers')
        }),
    )

    def get_formset(self, request, obj=None, **kwargs):
        if obj and obj.service_type == 'stt':
            return super().get_formset(request, obj, **kwargs)
        return super().get_formset(request, None, **kwargs)

    def has_add_permission(self, request, obj=None):
        return obj and obj.service_type == 'stt'

@admin.register(ExternalService)
class ExternalServiceAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'machine_name', 'service_type', 'is_default', 'is_enabled')
    list_filter = ('service_type', 'is_enabled', 'is_default')
    search_fields = ('machine_name', 'display_name', 'description')

    fieldsets = (
        (None, {
            'fields': ('display_name', 'machine_name', 'service_type', 'description')
        }),
        ('Connection & Orchestration', {
            'fields': ('service_url', 'container_name', 'is_enabled', 'is_default')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('machine_name',)
        return ()

    inlines = [STTModelSettingsInline]

    def get_inlines(self, request, obj=None):
        if obj:
            return self.inlines
        return []