from rest_framework import serializers

class TranscriptionRequestSerializer(serializers.Serializer):
    """
    Validates the simple request to transcribe a file.
    The orchestrator will handle selecting the appropriate service.
    """
    file_id = serializers.IntegerField(required=True, help_text="The ID of the UploadedFile to transcribe.")
    # The service_name field is now GONE. The API is simpler.