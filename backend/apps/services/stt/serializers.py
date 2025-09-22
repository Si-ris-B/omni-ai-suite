from rest_framework import serializers

class TranscriptionRequestSerializer(serializers.Serializer):
    """
    Validates the simple request to transcribe a file.
    The orchestrator will handle selecting the appropriate service.
    """
    file_id = serializers.IntegerField(required=True, help_text="The ID of the UploadedFile to transcribe.")
    # The service_name field is now GONE. The API is simpler.

class ProcessRequestSerializer(serializers.Serializer):
    """
    Validates the request for the unified 'process' endpoint.
    """
    source_type = serializers.ChoiceField(choices=['upload', 'youtube'], required=True)
    output_format = serializers.ChoiceField(choices=['srt', 'txt'], default='srt')
    url = serializers.URLField(required=False)

    def validate(self, data):
        """
        Check that 'url' is provided if source_type is 'youtube'.
        The presence of a file for 'upload' is checked in the view.
        """
        if data['source_type'] == 'youtube' and not data.get('url'):
            raise serializers.ValidationError({"url": "This field is required when source_type is 'youtube'."})
        return data