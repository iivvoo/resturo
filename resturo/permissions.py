from rest_framework import permissions
from .models import modelresolver


class IsStaffOrTargetUser(permissions.BasePermission):

    def has_permission(self, request, view):
        if view.action == 'retrieve':
            return True
        return request.user.is_staff

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj == request.user


class OrganizationPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return modelresolver('Membership').objects.filter(
            organization=view.get_object(), user=request.user).exists()
