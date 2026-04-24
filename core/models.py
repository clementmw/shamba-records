from django.db import models
# from .manager import CustomUserManager
from django.contrib.auth.models import AbstractUser, Permission
from django.utils import timezone
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType
import secrets
import uuid
# from encrypted_model_fields.fields import EncryptedTextField




class BaseModel(models.Model):
    """Abstract base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


