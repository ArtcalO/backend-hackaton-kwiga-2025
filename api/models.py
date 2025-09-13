from django.db import models
from django.contrib.auth.models import User
import os
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class UidModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True


class Profile(UidModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profile")
    def __str__(self):
        return f"{self.user} {self.uuid}"

class AuditLog(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.profile.user.username}: {self.action}"

class ObjectPermission(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)

    class Meta:
        unique_together = ('content_type', 'object_id', 'profile')

    def __str__(self):
        return f"Permissions for {self.content_object} by {self.profile.username}"


def user_directory_path(instance, filename):
    return f'user_{instance.owner.id}/{filename}'

class Folder(UidModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='subfolders', null=True, blank=True,)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='folders', null=True, blank=True)
    is_trashed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'parent', 'owner')

    def __str__(self):
        return self.name


class File(UidModel):
    name = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to=user_directory_path)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    size = models.BigIntegerField(null=True, blank=True)  # in bytes
    file_type = models.CharField(max_length=50, blank=True)  # e.g. pdf, jpg
    is_trashed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.size = self.file.size
        self.file_type = os.path.splitext(self.file.name)[1][1:].lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SharedFile(UidModel):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='shared_with')
    shared_with = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='shared_files')
    can_edit = models.BooleanField(default=False)
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('file', 'shared_with')

    def __str__(self):
        return f"{self.file.name} shared with {self.shared_with.username}"


class Gallery(UidModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='galleries')
    files = models.ManyToManyField(File, related_name='galleries')
    cover_image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, related_name='as_cover_for')
    is_public = models.BooleanField(default=False)  # Optional: to allow public sharing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'owner')

    def __str__(self):
        return self.name

class SharedGallery(UidModel):
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name='shared_with')
    shared_with = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='shared_galleries')
    can_edit = models.BooleanField(default=False)
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('gallery', 'shared_with')

    def __str__(self):
        return f"{self.gallery.name} shared with {self.shared_with.username}"
