from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import File, Folder, ObjectPermission, SharedFile, Gallery, SharedGallery

@receiver(post_save, sender=File)
@receiver(post_save, sender=Folder)
@receiver(post_save, sender=Gallery)
def assign_owner_permissions(sender, instance, created, **kwargs):
    if created and instance.owner:
        content_type = ContentType.objects.get_for_model(instance)
        ObjectPermission.objects.update_or_create(
            profile=instance.owner,
            content_type=content_type,
            object_id=instance.id,
            defaults={
                'can_view': True,
                'can_edit': True,
                'can_delete': True
            }
        )


@receiver(post_save, sender=SharedGallery)
@receiver(post_save, sender=SharedFile)
def assign_sharedgallery_permissions(sender, instance, **kwargs):
    content_type = ContentType.objects.get_for_model(instance.gallery)
    ObjectPermission.objects.update_or_create(
        profile=instance.shared_with,
        content_type=content_type,
        object_id=instance.gallery.id,
        defaults={
            'can_view': True,
            'can_edit': instance.can_edit,
            'can_delete': False
        }
    )