from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, TeacherProfile, StudentProfile, Course, Grade

# Register the Custom User model
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Roles', {'fields': ('is_student', 'is_teacher', 'is_admin')}),
    )
    list_display = ['username', 'email', 'is_student', 'is_teacher', 'is_admin']

admin.site.register(User, CustomUserAdmin)
admin.site.register(TeacherProfile)
admin.site.register(StudentProfile)
admin.site.register(Course)
admin.site.register(Grade)
