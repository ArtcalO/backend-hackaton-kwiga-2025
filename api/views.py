from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from .models import *
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from .permissions import IsOwnerOrReadOnly
from django.contrib.contenttypes.models import ContentType
from .utils import get_user_profile
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication


class CustomTokenView(TokenObtainPairView):
	serializer_class = CustomTokenSerializer

class ObjectPermissionViewSet(viewsets.ModelViewSet):
	queryset = ObjectPermission.objects.all()
	serializer_class = ObjectPermissionSerializer

	def get_queryset(self):
		return ObjectPermission.objects.filter(profile=get_user_profile(self.request.user))

class RootViewSet(viewsets.ViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	permission_classes = [permissions.IsAuthenticated]

	def list(self, request):
		profile = get_user_profile(request.user)
		files = File.objects.filter(folder__isnull=True, owner=profile)
		folders = Folder.objects.filter(parent__isnull=True, owner=profile)

		return Response({
			"files":FileSerializer(files, many=True, context={'request': request}).data,
			"folders":FolderSerializer(folders, many=True, context={'request': request}).data
		})

class ProfileViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	queryset = Profile.objects.all()
	serializer_class = ProfileSerializer
	permission_classes = permissions.IsAuthenticated,
	lookup_field = 'uuid'


	def get_queryset(self):
		user = self.request.user
		queryset = Profile.objects.all()
		if(user.is_superuser):
			return queryset
		try:
			pk = vars(self.request)["parser_context"]["kwargs"]["pk"]
			return queryset.filter(id=pk)
		except Exception:
			return None


class FolderViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	serializer_class = FolderSerializer
	permission_classes = [permissions.IsAuthenticated]
	lookup_field = 'uuid'

	def get_queryset(self):
		profile = get_user_profile(self.request.user)
		return Folder.objects.filter(
			models.Q(owner=profile)
		)
	
	def list(self, request, *args, **kwargs):
		queryset = self.get_queryset().filter(parent__isnull=True)
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)

	def perform_create(self, serializer):
		parent_folder = serializer.validated_data.get('parent', None)
		profile = get_user_profile(self.request.user)
		if parent_folder:
			if parent_folder.owner != profile:
				raise serializers.ValidationError("Vous ne pouvez pas ajouter un dossier dans un dossier qui ne vous appartient pas.")
		else:
			pass

		serializer.save(owner=profile)
	
	@action(detail=True, methods=['post'], url_path='share')
	def bulk_share(self, request, pk=None):
		folder = self.get_object()
		user_ids = request.data.get('users', [])
		can_edit = request.data.get('can_edit', False)

		folders_to_share = [folder] + list(get_all_descendants(folder))

		for user_id in user_ids:
			try:
				user = Profile.objects.get(pk=user_id)
				for f in folders_to_share:
					SharedFolder.objects.update_or_create(
						folder=f, shared_with=user,
						defaults={'can_edit': can_edit}
					)
					log_action(request.user, f"shared folder '{f.name}' with {user.username}")

					# Share all files in this folder
					for file in f.files.all():
						SharedFile.objects.update_or_create(
							file=file, shared_with=user,
							defaults={'can_edit': can_edit}
						)
						log_action(request.user, f"shared file '{file.name}' with {user.username}")
			except User.DoesNotExist:
				continue

		return Response({"status": "shared"}, status=status.HTTP_200_OK)

	@action(detail=True, methods=['delete'], url_path='share')
	def bulk_unshare(self, request, pk=None):
		folder = self.get_object()
		user_ids = request.data.get('users', [])
		folders_to_unshare = [folder] + list(get_all_descendants(folder))

		for user_id in user_ids:
			try:
				user = Profile.objects.get(pk=user_id)
				for f in folders_to_unshare:
					SharedFolder.objects.filter(folder=f, shared_with=user).delete()
					log_action(request.user, f"revoked folder '{f.name}' from {user.username}")

					for file in f.files.all():
						SharedFile.objects.filter(file=file, shared_with=user).delete()
						log_action(request.user, f"revoked file '{file.name}' from {user.username}")
			except User.DoesNotExist:
				continue

		return Response({"status": "unshared"}, status=status.HTTP_200_OK)

class FileViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	serializer_class = FileSerializer
	permission_classes = [permissions.IsAuthenticated]
	parser_classes = [MultiPartParser, FormParser]
	lookup_field = 'uuid'

	def get_queryset(self):
		profile = get_user_profile(self.request.user)
		qs = File.objects.filter(owner=profile, is_trashed=False) 

		# Prefetch ObjectPermission for all files in this queryset for this profile
		content_type = ContentType.objects.get_for_model(File)
		perms = ObjectPermission.objects.filter(
			profile=profile,
			content_type=content_type,
			object_id__in=qs.values_list('id', flat=True)
		)
		# Attach the permissions to each File object
		perm_map = {perm.object_id: perm for perm in perms}
		for obj in qs:
			obj._object_permission = perm_map.get(obj.id, None)

		return qs

	def perform_create(self, serializer):
		folder = serializer.validated_data.get('folder', None)
		profile = get_user_profile(self.request.user)
		print("profileeeeeeeeeee", profile)
		if folder:
			if folder.owner != profile:
				raise serializers.ValidationError("Vous ne pouvez pas ajouter un fichier dans un dossier qui ne vous appartient pas.")
		else:
			pass
		print("profileeeeeeeeeee", profile)
		serializer.save(owner=profile)

	
	@action(detail=True, methods=['post'], url_path='share')
	def bulk_share(self, request, pk=None):
		file = self.get_object()
		user_ids = request.data.get('users', [])
		can_edit = request.data.get('can_edit', False)

		for user_id in user_ids:
			try:
				profile = Profile.objects.get(pk=user_id)
				SharedFile.objects.update_or_create(
					file=file, shared_with=profile,
					defaults={'can_edit': can_edit}
				)
				# ObjectPermission will be handled by signals
				log_action(profile, f"shared file '{file.name}' with {profile.user.username}")
			except Profile.DoesNotExist:
				continue

		return Response({"status": "shared"}, status=status.HTTP_200_OK)

	@action(detail=True, methods=['delete'], url_path='share')
	def bulk_unshare(self, request, pk=None):
		file = self.get_object()
		user_ids = request.data.get('users', [])

		for user_id in user_ids:
			try:
				profile = Profile.objects.get(pk=user_id)
				SharedFile.objects.filter(file=file, shared_with=user).delete()
				log_action(profile, f"revoked access to file '{file.name}' from {profile.user.username}")
			except Profile.DoesNotExist:
				continue

		return Response({"status": "unshared"}, status=status.HTTP_200_OK)


class SharedFileViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	serializer_class = SharedFileSerializer
	permission_classes = [permissions.IsAuthenticated]
	lookup_field = 'uuid'

	def get_queryset(self):
		return SharedFile.objects.filter(file__owner=get_user_profile(self.request.user))


class GalleryViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	queryset = Gallery.objects.all()
	serializer_class = GallerySerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
	lookup_field = 'uuid'

	def perform_create(self, serializer):
		serializer.save(owner=get_user_profile(self.request.user))

	def get_queryset(self):
		return Gallery.objects.filter(owner=get_user_profile(self.request.user))


class SharedGalleryViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	queryset = SharedGallery.objects.all()
	serializer_class = SharedGallerySerializer
	permission_classes = [permissions.IsAuthenticated]
	lookup_field = 'uuid'

	def get_queryset(self):
		return SharedGallery.objects.filter(shared_with=get_user_profile(self.request.user))
