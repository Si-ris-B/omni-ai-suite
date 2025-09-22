# apps/services/views.py
from rest_framework import views, permissions
from rest_framework.response import Response
from .models import ExternalService


class ExternalServiceListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        service_type = request.GET.get('service_type')
        queryset = ExternalService.objects.filter(is_enabled=True)
        if service_type:
            queryset = queryset.filter(service_type=service_type)

        data = list(queryset.values())
        return Response(data)