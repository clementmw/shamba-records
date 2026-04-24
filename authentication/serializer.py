from rest_framework import serializers
from django.db import transaction
from .utility import *
from .models import *


class BaseSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20)
    first_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    kra_pin = serializers.CharField(max_length=11)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_phone_number(self, value):  # fixed: was validate_phone
        phone = value.replace(" ", "").replace("-", "")
        if not phone.startswith("+"):
            raise serializers.ValidationError(
                "Phone must be in E.164 format e.g. +254712345678"
            )
        return phone

    def validate_password(self, value):
        validate_password_strength(value)
        return value

    def validate_kra_pin(self, value):
        if User.objects.filter(kra_pin=value).exists():
            raise serializers.ValidationError("This KRA PIN is already registered.")
        return value


class AdminSignupSerializer(BaseSignupSerializer):
    def create(self, validated_data):
        from authentication.services.signup_service import build_user
        with transaction.atomic():
            return build_user(validated_data, role_category='ADMIN')


class AgentSignupSerializer(BaseSignupSerializer):
    def create(self, validated_data):
        from authentication.services.signup_service import build_user
        with transaction.atomic():
            user = build_user(validated_data, role_category='FIELD_AGENT')
            from field.models import Agents
            Agents.objects.create(user=user)
        
        return user



class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'kra_pin']


class UserProfileSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.category', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'role_name', 'is_active', 'date_joined',
            'email_verified', 'phone_number'
        ]
        read_only_fields = ['id', 'is_active', 'date_joined']


class AdminProfileSerializer(serializers.Serializer):
    """Placeholder — extend when Admin profile model is added"""
    pass


class AgentProfileSerializer(serializers.ModelSerializer):
    assigned_fields_count = serializers.SerializerMethodField()

    class Meta:
        from field.models import Agents  
        model = Agents
        fields = ['id', 'assigned_fields_count']

    def get_assigned_fields_count(self, obj):
        return obj.assigned_fields.count()