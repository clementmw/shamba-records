from .views import *
from django.urls import path

urlpatterns = [
    path('admin',  FieldManagementView.as_view(), name='assign-fields'),
    path('assign/<str:field_id>/', AssignFieldView.as_view(), name='get-fields'),
    path('agent', AgentFieldListView.as_view(), name='update-field'),
    path('agent/update/<str:field_id>', AgentFieldUpdateView.as_view(), name='update-field'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin dahboard'),
    path('agent/dashboard/', AgentDashboardView.as_view(), name='agent-dashboard'),
]
