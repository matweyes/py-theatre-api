from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """
    Allow read access to any request (including anonymous),
    but only allow write access to admin users.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsAdminOrOwner(BasePermission):
    """
    Admin can see everything.
    Authenticated users can only see/manage their own objects.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user
