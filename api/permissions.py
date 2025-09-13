# permissions.py
from rest_framework import permissions
from django.contrib.contenttypes.models import ContentType
from .models import ObjectPermission

def has_object_permission(profile, obj, permission_type='can_view'):
    if obj.owner == profile:
        return True
    content_type = ContentType.objects.get_for_model(obj)
    return ObjectPermission.objects.filter(
        content_type=content_type,
        object_id=obj.id,
        profile=profile,
        **{permission_type: True}
    ).exists()

def grant_full_permissions(profile, obj):
    content_type = ContentType.objects.get_for_model(obj)
    ObjectPermission.objects.update_or_create(
        profile=profile,
        content_type=content_type,
        object_id=obj.id,
        defaults={
            'can_view': True,
            'can_edit': True,
            'can_delete': True
        }
    )

class ReadOnlyRequiresAuth(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method == 'POST':
            return True
        return request.user and request.user.is_authenticated

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class CanViewObject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return has_object_permission(request.user, obj, 'can_view')

class CanEditObject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return has_object_permission(request.user, obj, 'can_edit')

class CanDeleteObject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return has_object_permission(request.user, obj, 'can_delete')

class CanCreateObject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return has_object_permission(request.user, obj, 'can_create')