from rest_framework import permissions

class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado que permite acceso a los usuarios con rol instructor
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.rol == 'instructor')