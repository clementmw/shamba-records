from .views import *
from django.urls import path,include

urlpatterns = [
    path('signup/', UserSignupupView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    
]