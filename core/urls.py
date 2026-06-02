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
    path('info/<str:info_type>/', views.info_page_view, name='info_page'),
    path('teacher/course/<int:course_id>/grades/', views.teacher_grades_view, name='teacher_grades'),
    path('teacher/course/<int:course_id>/attendance/', views.teacher_attendance_view, name='teacher_attendance'),
    path('student/report_card/download/', views.student_report_card_pdf, name='report_card_pdf'),
    path('research_hub/', views.research_hub_view, name='research_hub'),
    
    # Self-Enrollment Route
    path('student/enrollment/', views.student_enrollment_view, name='student_enrollment'),
]
