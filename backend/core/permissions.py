from rest_framework.permissions import BasePermission
from .models import RolePermission, UserRole


def get_user_permission_codes(user):
    if not user or not user.is_authenticated:
        return set()
    role_ids = UserRole.objects.filter(user=user).values_list("role_id", flat=True)
    permission_codes = RolePermission.objects.filter(role_id__in=role_ids).values_list(
        "permission__code", flat=True
    )
    return set(permission_codes)


class HasPermission(BasePermission):
    required_permission = None

    def has_permission(self, request, view):
        if request.user and request.user.is_superuser:
            return True
        permission = getattr(view, "required_permission", self.required_permission)
        if not permission:
            return True
        return permission in get_user_permission_codes(request.user)
