from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    @property
    def get_initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'is_teacher': True})
    subject_specialty = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"Teacher: {self.user.get_full_name() or self.user.username}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'is_student': True})
    roll_number = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    class_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15, blank=True) # New Field

    def __str__(self):
        return f"Student: {self.user.get_full_name() or self.user.username}"

class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, related_name='courses')
    students = models.ManyToManyField(StudentProfile, related_name='courses', blank=True)

    def __str__(self):
        return self.name

class Grade(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='grades')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.course.name}: {self.score}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username} at {self.timestamp}"

class Attendance(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance_records')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')])

    def __str__(self):
        return f"{self.student.user.username} - {self.course.name} - {self.date}: {self.status}"

class SchoolActivity(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    date = models.DateField()
    location = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['date']
        verbose_name_plural = "School Activities"

    def __str__(self):
        return self.title

class ResearchLog(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='research_logs')
    title = models.CharField(max_length=150)
    crop_type = models.CharField(max_length=100)
    soil_ph = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    moisture_level = models.CharField(max_length=50, blank=True)
    observations = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.title} - {self.crop_type} by {self.student.user.username}"
