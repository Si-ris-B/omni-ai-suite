# apps/services/api/serializers.py
from rest_framework import serializers

class ContainerControlSerializer(serializers.Serializer):
    """
    Validates the request to control a container.
    """
    service_name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="The name of the service as defined in docker-compose.yml"
    )
    action = serializers.ChoiceField(
        choices=['start', 'stop'],
        required=True,
        help_text="The action to perform on the service container."
    )