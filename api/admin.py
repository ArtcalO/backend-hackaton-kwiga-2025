from django.contrib import admin
from .models import Folder, File, SharedFile, Gallery, SharedGallery, Profile
# Register your models here.

admin.site.register(Folder)
admin.site.register(File)
admin.site.register(Profile)

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_public', 'created_at')
    list_filter = ('is_public',)

@admin.register(SharedGallery)
class SharedGalleryAdmin(admin.ModelAdmin):
    list_display = ('gallery', 'shared_with', 'can_edit', 'shared_at')