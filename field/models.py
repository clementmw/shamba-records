from django.db import models
from django.contrib.auth.models import AbstractUser, Permission,PermissionsMixin
from django.utils import timezone
from datetime import timedelta
from .utility import *
from django.contrib.contenttypes.models import ContentType
import secrets
from core.models import BaseModel


class FieldManagement(BaseModel):
    FARMING_STAGES = (
        ('planted', 'Planted'),
        ('growing', 'Growing'),
        ('ready', 'Ready'),
        ('harvested', 'Harvested'),
    )
    FIELD_STATUS = (
        ('active', 'Active'),
        ('at_risk', 'At Risk'),
        ('completed', 'Completed'),
    )

    name = models.CharField(max_length=50, null=True, blank=True)
    crop_type = models.CharField(max_length=50, null=True, blank=True)
    planting_date = models.DateField(null=True, blank=True)
    current_stage = models.CharField(max_length=50, choices=FARMING_STAGES, default='planted')
    field_status = models.CharField(max_length=50, choices=FIELD_STATUS, default='active')
    review = models.TextField(null=True, blank=True)
    review_at = models.DateTimeField(null=True, blank=True)
    assigned_agent = models.ForeignKey(
        'Agents',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fields'
    )
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_fields'
    )

    def __str__(self):
        return f"{self.name} - {self.crop_type}"


class Agents(BaseModel):
    user = models.OneToOneField(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name="agent_profile"
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.user.email}"