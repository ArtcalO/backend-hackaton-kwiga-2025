from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import *
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .utils import log_action, get_user_profile

class CustomTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super(CustomTokenSerializer, self).validate(attrs)
        data['is_admin'] = self.user.is_superuser
        data['id'] = self.user.id
        data['first_name'] = self.user.first_name
        data['last_name'] = self.user.last_name

        return data

class ObjectPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectPermission
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
	password = serializers.CharField(write_only=True)
	
	class Meta:
		model = User
		exclude = "last_login", "is_superuser", "groups", "is_staff", "is_active", "date_joined", "user_permissions"
		depth = 1
		extra_kwargs = {
			'username': {'validators': []},
		}

class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username',
        allow_null=True,
        required=False,
    )
    class Meta:
        model = Profile
        fields = ['uuid', 'user']
    

class FileSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    folder = serializers.SlugRelatedField(
        queryset=Folder.objects.all(),
        slug_field='uuid',
        allow_null=True,
        required=False,
    )
    owner = serializers.SlugRelatedField(
        queryset=Profile.objects.all(),
        slug_field='uuid',
        allow_null=True,
        required=False,
    )
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = File
        fields = [
            'uuid', 'name', 'file', 'folder', 'owner', 'size', 
            'file_type', 'is_trashed', 'created_at', 'updated_at',
            'permissions'  # Add permissions here
        ]
        read_only_fields = ['owner', 'size', 'file_type', 'created_at', 'updated_at']

    def validate(self, attrs):
        if not attrs.get('name') and attrs.get('file'):
            attrs['name'] = attrs['file'].name
        return attrs

    def get_permissions(self, obj):
        profile = get_user_profile(self.context['request'].user)
        perm = getattr(obj, '_object_permission', None)
        if perm:
            return {
                'can_view': perm.can_view,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete,
            }
        from .models import ObjectPermission
        content_type = ContentType.objects.get_for_model(obj)
        try:
            perm = ObjectPermission.objects.get(
                profile=profile,
                content_type=content_type,
                object_id=obj.id
            )
            return {
                'can_view': perm.can_view,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete,
            }
        except ObjectPermission.DoesNotExist:
            if obj.owner == profile:
                return {'can_view': True, 'can_edit': True, 'can_delete': True}
            return {'can_view': False, 'can_edit': False, 'can_delete': False}


class ShallowFolderSerializer(serializers.ModelSerializer):
    files = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = [
            'uuid', 'name', 'parent', 'owner', 'is_trashed',
            'created_at', 'updated_at', 'files', 'permissions'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']

    def get_files(self, obj):
        files_qs = obj.files.filter(is_trashed=False)
        return FileSerializer(files_qs, many=True, context=self.context).data

    def get_permissions(self, obj):
        print(dir(self.context))
        perm = getattr(obj, '_object_permission', None)
        if perm:
            return {
                'can_view': perm.can_view,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete,
            }
        profile = get_user_profile(self.context['request'].user)
        if obj.owner == profile:
            return {'can_view': True, 'can_edit': True, 'can_delete': True}
        return {'can_view': False, 'can_edit': False, 'can_delete': False}


class FolderSerializer(serializers.ModelSerializer):
    subfolders = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    parent = serializers.SlugRelatedField(
        queryset=Folder.objects.all(),
        slug_field='uuid',
        required=False,
        allow_null=True
    )
    owner = serializers.SlugRelatedField(
        queryset=Profile.objects.all(),
        slug_field='uuid',
        required=False,
        allow_null=True
    )
    class Meta:
        model = Folder
        fields = [
            'uuid', 'name', 'parent', 'owner', 'is_trashed',
            'created_at', 'updated_at', 'subfolders', 'files', 'permissions'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']

    def get_files(self, obj):
        files_qs = getattr(obj, '_prefetched_files', obj.files.filter(is_trashed=False))
        serializer = FileSerializer(files_qs, many=True, context=self.context)
        return serializer.data

    def get_permissions(self, obj):
        # Try to use prefetched permission on obj if available
        profile = get_user_profile(self.context['request'].user)
        perm = getattr(obj, '_object_permission', None)
        if perm:
            return {
                'can_view': perm.can_view,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete,
            }
        from .models import ObjectPermission
        content_type = ContentType.objects.get_for_model(obj)
        try:
            perm = ObjectPermission.objects.get(
                profile=profile,
                content_type=content_type,
                object_id=obj.id
            )
            return {
                'can_view': perm.can_view,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete,
            }
        except ObjectPermission.DoesNotExist:
            if obj.owner == profile:
                return {'can_view': True, 'can_edit': True, 'can_delete': True}
            return {'can_view': False, 'can_edit': False, 'can_delete': False}

    def get_subfolders(self, obj):
        direct_subfolders = obj.subfolders.filter(is_trashed=False)
        for folder in direct_subfolders:
            folder._object_permission = getattr(folder, '_object_permission', None)

        return ShallowFolderSerializer(
            direct_subfolders,
            many=True,
            context=self.context
        ).data


class SharedFileSerializer(serializers.ModelSerializer):
    file = FileSerializer(read_only=True)
    file_id = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), source='file', write_only=True)
    shared_with = serializers.SlugRelatedField(slug_field='uuid', queryset=Profile.objects.all())

    class Meta:
        model = SharedFile
        fields = ['uuid', 'file', 'file_id', 'shared_with', 'can_edit', 'shared_at']
        read_only_fields = ['shared_at']


class GallerySerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.uuid')
    files = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True)
    cover_image = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), allow_null=True)

    class Meta:
        model = Gallery
        fields = ['uuid', 'name', 'description', 'owner', 'files', 'cover_image', 'is_public', 'created_at', 'updated_at']


class SharedGallerySerializer(serializers.ModelSerializer):
    shared_with = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all())
    gallery = serializers.PrimaryKeyRelatedField(queryset=Gallery.objects.all())

    class Meta:
        model = SharedGallery
        fields = ['uuid', 'gallery', 'shared_with', 'can_edit', 'shared_at']