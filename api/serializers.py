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
    uploaded_by = serializers.SlugRelatedField(
        queryset=Profile.objects.all(),
        slug_field='uuid',
        allow_null=True,
        required=False,
    )
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = File
        fields = [
            'uuid', 'name', 'file', 'uploaded_by', 'size','course' ,
            'file_type', 'is_trashed', 'created_at', 'updated_at',
        ]
        read_only_fields = ['uploaded_by', 'size', 'file_type', 'created_at', 'updated_at']

    def validate(self, attrs):
        if not attrs.get('name') and attrs.get('file'):
            attrs['name'] = attrs['file'].name
        return attrs


class AcademicYearSerializer(serializers.ModelSerializer):
   class Meta:
        model = AcademicYear
        fields = "__all__"

class DegreeSerializer(serializers.ModelSerializer):
   class Meta:
        model = Degree
        fields = "__all__"

class UniversitySerializer(serializers.ModelSerializer):
   class Meta:
        model = University
        fields = "__all__"

class AcademicDegreeSerializer(serializers.ModelSerializer):
   class Meta:
        model = AcademicDegree
        fields = "__all__"

class FacultySerializer(serializers.ModelSerializer):
   class Meta:
        model = Faculty
        fields = "__all__"

class DepartmentSerializer(serializers.ModelSerializer):
   class Meta:
        model = Department
        fields = "__all__"

class CourseSerializer(serializers.ModelSerializer):
   class Meta:
        model = Course
        fields = "__all__"