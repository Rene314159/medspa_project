from rest_framework import serializers
from .models import Medspa, Service, Appointment, AppointmentServices

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'medspa', 'name', 'description', 'price', 'duration']
        read_only_fields = ['id']

class MedspaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medspa
        fields = ['id', 'name', 'address', 'phone_number', 'email']
        read_only_fields = ['id']

class AppointmentSerializer(serializers.ModelSerializer):
    # Allow writing a list of service IDs during creation/update
    service_ids = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), many=True, write_only=True, required=True
    )
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'user', 'medspa', 'start_time', 'total_duration',
            'total_price', 'status', 'service_ids', 'services'
        ]
        read_only_fields = ['id', 'total_duration', 'total_price']

    def create(self, validated_data):
        # Pop the service IDs from validated data
        service_ids = validated_data.pop('service_ids')
        from django.db import transaction
        with transaction.atomic():
            # Create the appointment (initially without totals)
            appointment = Appointment.objects.create(**validated_data)
            total_price = 0
            total_duration = 0
            # Link services and accumulate totals
            for service in service_ids:
                # Create join record (or use appointment.services.add(service) if using a ManyToManyField)
                AppointmentServices.objects.create(appointment=appointment, service=service)
                total_price += service.price if service.price else 0
                total_duration += service.duration if service.duration else 0
            # Update appointment totals
            appointment.total_price = total_price
            appointment.total_duration = total_duration
            appointment.save()
        return appointment

    def update(self, instance, validated_data):
        service_ids = validated_data.pop('service_ids', None)
        from django.db import transaction
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if service_ids is not None:
                # Remove existing service associations
                AppointmentServices.objects.filter(appointment=instance).delete()
                total_price = 0
                total_duration = 0
                # Re-add the provided services and recalc totals
                for service in service_ids:
                    AppointmentServices.objects.create(appointment=instance, service=service)
                    total_price += service.price if service.price else 0
                    total_duration += service.duration if service.duration else 0
                instance.total_price = total_price
                instance.total_duration = total_duration
                instance.save()
        return instance
