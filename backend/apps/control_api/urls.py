from django.urls import path
from .views import ServiceStatusView, ServiceStartView, ServiceStopView

app_name = 'control_api'

urlpatterns = [
    path('status/<str:service_name>/', ServiceStatusView.as_view(), name='service-status'),
    path('start/<str:service_name>/', ServiceStartView.as_view(), name='service-start'),
    path('stop/<str:service_name>/', ServiceStopView.as_view(), name='service-stop'),
]