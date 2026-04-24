from authentication.models import User, Role


def build_user(validated_data: dict, role_category: str) -> User:
    try:
        role = Role.objects.get(category=role_category, is_system_role=False)
    except Role.DoesNotExist:
        raise ValueError(
            f"No Role found for category '{role_category}'. "
        )
    except Role.MultipleObjectsReturned:
        role = Role.objects.filter(
            category=role_category,
            is_system_role=False,
        ).order_by('created_at').first()

    user = User(
        email = validated_data['email'],
        first_name=validated_data.get('first_name', ''),
        last_name=validated_data.get('last_name', ''),
        role = role,
        is_active = False,   # activated after email verification
        phone_number = validated_data.get('phone_number', ''),
        kra_pin = validated_data.get('kra_pin',''),
    )
    user.set_password(validated_data['password'])
    user.save()

    return user