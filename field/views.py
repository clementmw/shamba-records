from django.shortcuts import render
from .models import *
from .serializer import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from authentication.permissions import IsAdminUser, IsFieldAgent



class FieldManagementView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            fields = FieldManagement.objects.select_related('assigned_agent__user').all()
            paginator = CustomPagination()
            paginated_fields = paginator.paginate_queryset(fields, request)
            serializer = FieldManagementSerializer(paginated_fields, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Admin creates a new field"""
        try:
            serializer = FieldManagementSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(created_by=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssignFieldView(APIView):
    """Admin: Assign or unassign a field to an agent"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, field_id):
        try:
            field = FieldManagement.objects.get(id=field_id)
        except FieldManagement.DoesNotExist:
            return Response({'error': 'Field not found'}, status=status.HTTP_404_NOT_FOUND)

        agent_id = request.data.get('agent_id')

        # agent_id=None means unassign
        if agent_id is None:
            field.assigned_agent = None
            field.save()
            return Response({'message': 'Field unassigned successfully'}, status=status.HTTP_200_OK)

        try:
            agent = Agents.objects.get(id=agent_id)
        except Agents.DoesNotExist:
            return Response({'error': 'Agent not found'}, status=status.HTTP_404_NOT_FOUND)

        field.assigned_agent = agent
        field.save()
        return Response({'message': f'Field assigned to {agent.user.get_full_name()} successfully'}, status=status.HTTP_200_OK)


class AgentFieldListView(APIView):
    """Field Agent: View their assigned fields"""
    permission_classes = [IsAuthenticated, IsFieldAgent]

    def get(self, request):
        try:
            agent = Agents.objects.get(user=request.user)
            fields = FieldManagement.objects.filter(assigned_agent=agent).order_by('-created_at')
            serializer = FieldManagementSerializer(fields, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Agents.DoesNotExist:
            return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AgentFieldUpdateView(APIView):
    """Field Agent: Update stage and notes on their assigned field"""
    permission_classes = [IsAuthenticated, IsFieldAgent]

    def patch(self, request, field_id):
        try:
            agent = Agents.objects.get(user=request.user)
            field = FieldManagement.objects.get(id=field_id, assigned_agent=agent)

            serializer = FieldUpdateSerializer(field, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Agents.DoesNotExist:
            return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)
        except FieldManagement.DoesNotExist:
            return Response({'error': 'Field not found or not assigned to you'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminDashboardView(APIView):
    """Admin: Summary stats across all fields"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            fields = FieldManagement.objects.all()
            total = fields.count()

            status_breakdown = {
                'active': fields.filter(field_status='active').count(),
                'at_risk': fields.filter(field_status='at_risk').count(),
                'completed': fields.filter(field_status='completed').count(),
            }
            stage_breakdown = {
                'planted': fields.filter(current_stage='planted').count(),
                'growing': fields.filter(current_stage='growing').count(),
                'ready': fields.filter(current_stage='ready').count(),
                'harvested': fields.filter(current_stage='harvested').count(),
            }

            return Response({
                'total_fields': total,
                'unassigned_fields': fields.filter(assigned_agent=None).count(),
                'status_breakdown': status_breakdown,
                'stage_breakdown': stage_breakdown,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AgentDashboardView(APIView):
    """Field Agent: Summary stats for their fields"""
    permission_classes = [IsAuthenticated, IsFieldAgent]

    def get(self, request):
        try:
            agent = Agents.objects.get(user=request.user)
            fields = FieldManagement.objects.filter(assigned_agent=agent)
            total = fields.count()

            status_breakdown = {
                'active': fields.filter(field_status='active').count(),
                'at_risk': fields.filter(field_status='at_risk').count(),
                'completed': fields.filter(field_status='completed').count(),
            }
            stage_breakdown = {
                'planted': fields.filter(current_stage='planted').count(),
                'growing': fields.filter(current_stage='growing').count(),
                'ready': fields.filter(current_stage='ready').count(),
                'harvested': fields.filter(current_stage='harvested').count(),
            }

            return Response({
                'total_fields': total,
                'status_breakdown': status_breakdown,
                'stage_breakdown': stage_breakdown,
            }, status=status.HTTP_200_OK)

        except Agents.DoesNotExist:
            return Response({'error': 'Agent profile not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)