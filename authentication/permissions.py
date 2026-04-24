from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    message = "Access restricted to Admin users only."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role.category == 'ADMIN'
        )


class IsFieldAgent(permissions.BasePermission):
    message = "Access restricted to Field Agents only."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role.category == 'FIELD_AGENT'
        )