from django.db import models
from .manager import CustomUserManager
from django.contrib.auth.models import AbstractUser, Permission,PermissionsMixin
from django.utils import timezone
from datetime import timedelta
from .utility import *
from django.contrib.contenttypes.models import ContentType
import secrets
from core.models import BaseModel




class Role(BaseModel):
    
    ROLE_CATEGORIES = (
        ('ADMIN', 'Admin'),
        ('FIELD_AGENT','Field Agent'),
    )

    role_name = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=50, choices=ROLE_CATEGORIES, default='FIELD_AGENT',null=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name='role permissions',
        blank=True,
        related_name='roles'
    )
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False)


    class Meta:
        db_table = 'auth_role'
        indexes = [
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.role_name 
    
class User(AbstractUser,BaseModel):
    role = models.ForeignKey(Role, on_delete=models.PROTECT,related_name="users")
    phone_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True, null=True)
    email_verification_expiry = models.DateTimeField(blank=True, null=True)
    password = models.CharField(max_length=128)
    kra_pin = models.CharField(max_length=11,unique=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)

 
    username = None
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()



    def generate_email_token(self):
        """Generate token for email verification"""
        token = secrets.token_hex(32)
        self.email_verification_token = token
        self.email_verification_expiry = timezone.now() + timedelta(hours=24)
        self.save()
        return token

    def verify_email(self, token):
        """Return True if token valid and email is verified"""
        if (
            self.email_verification_token == token and
            timezone.now() < self.email_verification_expiry
        ):
            self.is_active = True
            self.email_verified = True
            self.email_verification_token = None
            self.email_verification_expiry = None
            self.save()
            return True
        return False

    @property
    def is_locked(self) -> bool:
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False


    def __str__(self):
        return f"{self.first_name} - {self.role} - {self.last_name} - {self.email}"
    
    class Meta:
        indexes = [
            models.Index(fields=['email', 'role']),
            models.Index(fields=['role', 'is_active'])
        ]


class OTPPurpose(models.TextChoices):
    PHONE_VERIFY = "phone_verify","Phone verification"
    LOGIN = "login","Login OTP"
    PASSWORD_RESET = "password_reset","Password reset"
 
 
class OTPRecord(BaseModel):
    user= models.ForeignKey(User, on_delete=models.CASCADE,related_name="otp_records")
    purpose    = models.CharField(max_length=20, choices=OTPPurpose.choices)
    code_hash  = models.CharField(max_length=128)  # bcrypt hash — never store plaintext
    otp_expiry = models.DateTimeField()
    used_at    = models.DateTimeField(null=True, blank=True)
    attempts   = models.PositiveSmallIntegerField(default=0)  # max 3 attempts
 
    class Meta:
        db_table = "auth_otp_record"
        indexes  = [models.Index(fields=["user", "purpose", "otp_expiry"])]
 
    @property
    def is_used(self):
        return self.used_at is not None
    

