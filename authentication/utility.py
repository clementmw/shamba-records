import random
import string
import datetime
import uuid
from rest_framework import pagination
import secrets

def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"

    if not any(char in string.punctuation for char in password):
        return False, "Password must contain at least one special character"

    return True, None