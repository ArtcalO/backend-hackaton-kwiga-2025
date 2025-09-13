from .models import AuditLog, Profile

def log_action(profile, action):
    AuditLog.objects.create(user=profile, action=action)

def get_all_descendants(folder):
    for subfolder in folder.subfolders.all():
        yield subfolder
        yield from get_all_descendants(subfolder)

def get_user_profile(user):
    if user:
        profile, _ = Profile.objects.get_or_create(user=user)
        return profile
    return None

