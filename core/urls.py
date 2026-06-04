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
    path('teacher/timetable/', views.teacher_timetable_view, name='teacher_timetable'),
    path('student/fees/', views.student_fees_view, name='student_fees'),
    path('student/fees/receipt/', views.student_fee_receipt_pdf, name='student_fee_receipt'),
    path('teacher/student/<int:student_id>/reminder/', views.teacher_send_fee_reminder, name='send_fee_reminder'),
    path('teacher/student/<int:student_id>/suspend/', views.teacher_suspend_student, name='suspend_student'),
    path('student/fees/pay/demo/', views.student_fees_pay_demo_view, name='student_fees_pay_demo'),
    path('teacher/student/<int:student_id>/reenroll/', views.teacher_reenroll_student_view, name='teacher_reenroll_student'),
    path('homework/', views.homework_hub_view, name='homework_hub'),
    path('homework/submit/<int:assignment_id>/', views.student_submit_homework_view, name='student_submit_homework'),
    path('homework/grade/<int:submission_id>/', views.teacher_grade_homework_view, name='teacher_grade_homework'),
    
    # New Homework Receipt PDF Route
    path('homework/submission/<int:submission_id>/receipt/', views.student_homework_receipt_pdf, name='homework_receipt_pdf'),
]
