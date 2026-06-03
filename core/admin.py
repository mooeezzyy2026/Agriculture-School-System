from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, TeacherProfile, StudentProfile, Course, Grade, Attendance, SchoolActivity

# --- CUSTOM ADMINISTRATOR PANEL BRANDING ---
admin.site.site_header = 'Agriculture School Admin'
admin.site.site_title = 'Agriculture Portal Admin'
admin.site.index_title = 'System Database & Portal Control Panel'

# Custom User Admin to manage student, teacher, and admin flags in the roster list
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('System Roles', {'fields': ('is_student', 'is_teacher', 'is_admin')}),
    )
    list_display = ['username', 'first_name', 'last_name', 'is_student', 'is_teacher', 'is_admin']
    list_filter = ['is_student', 'is_teacher', 'is_admin', 'is_active']

# Register the models cleanly in the admin interface
admin.site.register(User, CustomUserAdmin)
admin.site.register(TeacherProfile)
admin.site.register(StudentProfile)
admin.site.register(Course)
admin.site.register(Grade)
admin.site.register(Attendance)
admin.site.register(SchoolActivity)
