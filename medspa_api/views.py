from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

from .models import Service, Appointment
from .serializers import ServiceSerializer, AppointmentSerializer

# Custom permission: only allow the owner (or medspa admin) to modify a record.
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an attribute 'user'.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions only for the owner.
        return obj.user == request.user

class ServiceViewSet(viewsets.ModelViewSet):
    """
    CRUD for Services.
    - Create: Requires a medspa association.
    - Update: Allows changing name, description, price, and duration.
    - Retrieve: Get a service by its ID.
    - List: Optionally filter by medspa.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        # If a query parameter 'medspa_id' is provided, filter by it.
        medspa_id = self.request.query_params.get('medspa_id')
        if medspa_id:
            queryset = queryset.filter(medspa_id=medspa_id)
        return queryset

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    CRUD for Appointments.
    - Create: Accepts a list of service IDs; computes total_price and total_duration.
    - Retrieve: Get appointment details.
    - Update: Allows status changes (e.g., scheduled -> completed/canceled).
    - List: Supports filtering by status and by start_date.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['start_time']

    def get_queryset(self):
        """
        Only return appointments for the logged-in user (unless admin).
        Also, support filtering by start_date via a query parameter.
        """
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        # Filter by date if provided (e.g., ?date=2025-02-18)
        date_param = self.request.query_params.get('date')
        if date_param:
            qs = qs.filter(start_time__date=date_param)
        return qs

    def create(self, request, *args, **kwargs):
        # Use atomic transaction to ensure concurrency safety.
        with transaction.atomic():
            return super().create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        # Allow partial updates, but if services are updated, recalc totals.
        with transaction.atomic():
            return super().partial_update(request, *args, **kwargs)