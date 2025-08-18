# backend/apps/features/uploader/api/serializers.py

# backend/apps/features/uploader/api/serializers.py
from rest_framework import serializers
from ..models import UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    """
    Handles the validation and creation of UploadedFile objects.
    The view is responsible for providing the 'original_modified_at' value.
    This serializer is responsible for extracting 'original_filename' from the file object.
    """

    class Meta:
        model = UploadedFile
        fields = [
            'id',
            'file',
            'original_filename',
            'file_type',
            'created_at',
            'original_modified_at',
        ]
        # 'original_filename' is set in the create method, so it's read-only for the API client.
        # 'original_modified_at' is now provided by the view, so it is writable on create.
        read_only_fields = [
            'id',
            'original_filename',
            'created_at',
        ]

    def create(self, validated_data):
        """
        Overrides the default create method to set the original_filename from the file object.
        """
        uploaded_file_obj = validated_data.get('file')
        validated_data['original_filename'] = uploaded_file_obj.name

        # Call the parent's create method, which will now work correctly
        # with our simplified get_upload_path model function.
        return super().create(validated_data)