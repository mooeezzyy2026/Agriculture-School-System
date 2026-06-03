from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    path('', views.login_redirect_view, name='login_redirect'),
    path('student/dashboard/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('teacher/dashboard/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('messages/', views.messages_view, name='messages'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('teacher/course/<int:course_id>/grades/', views.teacher_grades_view, name='teacher_grades'),
    path('teacher/course/<int:course_id>/attendance/', views.teacher_attendance_view, name='teacher_attendance'),
    path('student/report_card/download/', views.student_report_card_pdf, name='report_card_pdf'),
    path('student/enrollment/', views.student_enrollment_view, name='student_enrollment'),
    path('student/timetable/', views.student_timetable_view, name='student_timetable'),
    path('student/course/<int:course_id>/drop/', views.student_drop_course_view, name='student_drop_course'),
    path('teacher/students/', views.student_directory_view, name='student_directory'),
    path('teacher/student/<int:student_id>/', views.student_detail_view, name='student_detail'),
    
    # New Teacher Timetable Route
    path('teacher/timetable/', views.teacher_timetable_view, name='teacher_timetable'),
]
