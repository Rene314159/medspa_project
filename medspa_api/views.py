from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Sum

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

from .models import Service, Appointment, Medspa, AppointmentServices, User
from .serializers import ServiceSerializer, AppointmentSerializer, MedspaSerializer

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['medspa']

    def get_queryset(self):
        queryset = super().get_queryset()
        medspa_id = self.request.query_params.get('medspa_id')
        if medspa_id:
            queryset = queryset.filter(medspa_id=medspa_id)
        return queryset

    def create(self, request, *args, **kwargs):
        if 'medspa' not in request.data:
            return Response(
                {'medspa': 'Medspa ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    CRUD for Appointments.
    - Create: Accepts a list of service IDs; computes total_price and total_duration.
    - Retrieve: Get appointment details.
    - Update: Allows status changes (scheduled -> completed/canceled).
    - List: Supports filtering by status and date.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['start_time']

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        
        date_param = self.request.query_params.get('date')
        if date_param:
            qs = qs.filter(start_time__date=date_param)
        return qs

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            # Debug information
            print("Request data before:", request.data)
            print("User ID from request:", request.user.id)
            print("User is authenticated:", request.user.is_authenticated)
            
            try:
                user = User.objects.get(id=1)
                print("User exists in DB:", user.id, user.username)
            except User.DoesNotExist:
                print("User with ID 1 does not exist in DB")

            # Validate services exist and belong to same medspa
            service_ids = request.data.get('service_ids', [])
            if not service_ids:
                return Response(
                    {'service_ids': 'At least one service is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            services = Service.objects.filter(id__in=service_ids)
            if len(services) != len(service_ids):
                return Response(
                    {'service_ids': 'Invalid service IDs provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate totals
            totals = services.aggregate(
                total_duration=Sum('duration'),
                total_price=Sum('price')
            )

            # Prepare the data
            data = request.data.copy()  # Make a mutable copy
            data['total_duration'] = totals['total_duration'] or 0
            data['total_price'] = totals['total_price'] or 0
            data['status'] = 'scheduled'
            data['user'] = request.user.id

            # Create serializer with modified data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            print("Final data being saved:", data)
            
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED, 
                headers=headers
            )

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            
            # Validate status transitions
            new_status = request.data.get('status')
            if new_status and new_status not in dict(Appointment.STATUS_CHOICES):
                return Response(
                    {'status': f'Status must be one of {dict(Appointment.STATUS_CHOICES).keys()}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # If services are being updated, recalculate totals
            if 'service_ids' in request.data:
                service_ids = request.data.get('service_ids', [])
                services = Service.objects.filter(id__in=service_ids)
                
                if len(services) != len(service_ids):
                    return Response(
                        {'service_ids': 'Invalid service IDs provided'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Recalculate totals
                totals = services.aggregate(
                    total_duration=Sum('duration'),
                    total_price=Sum('price')
                )
                request.data['total_duration'] = totals['total_duration'] or 0
                request.data['total_price'] = totals['total_price'] or 0

            return super().partial_update(request, *args, **kwargs)

class MedspaViewSet(viewsets.ModelViewSet):
    """
    CRUD for Medspas.
    - Create: Add a new medspa record.
    - Retrieve: Get a medspa record by ID.
    - Update: Modify medspa details.
    - List: Get all medspas.
    """
    queryset = Medspa.objects.all()
    serializer_class = MedspaSerializer
    permission_classes = [permissions.IsAuthenticated]



User = get_user_model()

class CustomAuthToken(ObtainAuthToken):
    """
    Custom authentication view that allows users to log in using email instead of username.
    """
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=400)

        # Authenticate using email instead of username
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=400)

        if not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=400)

        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})

