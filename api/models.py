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

class AcademicYear(models.Model):
    start = models.DateField()
    end = models.DateField()

    def __str__(self):
        return f"{self.start}/{self.end}"   

class Degree(models.Model):
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name
class University(models.Model):
    name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=50)
    logo = models.ImageField(upload_to="universities/logo")
    address = models.CharField(max_length=200)
    site_web = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"
class AcademicDegree(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    degree = models.ForeignKey(Degree, on_delete=models.CASCADE)
    year = models.CharField(max_length=4)
    code = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"{self.degree} {self.year}"
    

class Faculty(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    code = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"

class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.faculty} {self.name}"

class Course(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    academic_degree = models.ForeignKey(AcademicDegree, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name}"
class File(UidModel):
    
    FILE_CATEGORY = [
		('course', 'Cours'),
		('exam', 'Examen'),
		('correction', 'Correction'),
		('essay', 'Mémoire'),
	]
        
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to="fichiers/", null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    size = models.BigIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=50, blank=True)
    file_category = models.CharField(max_length=20, choices=FILE_CATEGORY, default='cours')
    is_trashed = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    nb_retrieved = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
            self.file_type = os.path.splitext(self.file.name)[1][1:].lower()
        elif self.text:
            self.file_type = ".txt"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title