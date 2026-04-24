from django.shortcuts import render
from .models import *
from .serializer import *
from .utility import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import update_last_login
from django.db import transaction
import logging

logger = logging.getLogger(__name__)



SIGNUP_SERIALIZER = {
    'ADMIN': AdminSignupSerializer,
    'FIELD_AGENT': AgentSignupSerializer,
}

PROFILE_SERIALIZER = {
    'ADMIN': AdminProfileSerializer,
    'FIELD_AGENT': AgentProfileSerializer,
}

def serialize_full_user(user):
    # Serialize basic user data
    user_data = UserProfileSerializer(user).data
    
    # Get the role name from the ForeignKey relationship
    role_name = user.role.category  
    

    
    # Get the appropriate serializer class for the role
    serializer_class = PROFILE_SERIALIZER.get(role_name)
    
    if serializer_class:
        # Get the profile object based on role
        profile_obj = None
        if role_name == 'FIELD_AGENT':
            profile_obj = getattr(user, 'agent_profile', None)
        elif role_name in ['ADMIN']:
            profile_obj = getattr(user, 'admin_profile', None)

        
        # Serialize profile data if exists
        if profile_obj:
            profile_data = serializer_class(profile_obj).data
            profile_data.pop('user', None)  
            user_data['profile'] = profile_data
        else:
            user_data['profile'] = None
    
    user_data['role_name'] = role_name
    
    return user_data


class UserSignupupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data

            user_type = data.get('user_type')

            if not user_type:
                return Response({"error": "user_type is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer_class = SIGNUP_SERIALIZER.get(user_type)

            if not serializer_class:
                return Response({"error": "Invalid user_type"}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = serializer_class(data=data)

            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                try:
                    
                    user = serializer.save()
                                  
                except ValueError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
            # send_verification_email.delay(str(user.id),request.headers.get('Origin'))
            # send_welcome_email.delay(user.id)
            return Response({
                "message": "User created successfully",
                "user_id": user.id,
                "user_type": user.role.category,
                "is_active":user.is_active
                                
                }, status=status.HTTP_201_CREATED)
    
        except Exception as e:
            logger.info(f"Error during user signup: {str(e)}" )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class UserLoginView(APIView):
    def post(self,request):
        try:
            data = request.data
            email = data.get('email').lower()
            password = data.get('password')

            if not email or not password:
                return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                get_user = User.objects.get(email=email)

                if not get_user.check_password(password):
                    return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
                
                if not get_user.email_verified:
                    return Response({'error': 'Please verify your email before logging in.'}, status=status.HTTP_401_UNAUTHORIZED)
                
                if not get_user.is_active:
                    return Response({"error": "Account is deactivated. Please contact support."}, status=status.HTTP_401_UNAUTHORIZED)
                
                
                if get_user.role.category in ('SYSTEM', 'STAFF'):
                    return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
                
                update_last_login(None,get_user)

                refresh = RefreshToken.for_user(get_user)
                user_data = serialize_full_user(get_user)

                return Response({
                    "message": "Login successful",
                    "user": user_data,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    }
                })
            except User.DoesNotExist:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED) 

        except Exception as e:
            logger.error(f"Error during user login: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)