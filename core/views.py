import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.db.models import Avg
from django.http import HttpResponse
from django.contrib import messages
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from .models import Course, Grade, Message, User, StudentProfile, Attendance, SchoolActivity, FeeRecord, Assignment, AssignmentSubmission

@login_required
def login_redirect_view(request):
    if request.user.is_student: return redirect('student_dashboard')
    elif request.user.is_teacher: return redirect('teacher_dashboard')
    else: return redirect('analytics')

class StudentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/student_dashboard.html'
    def test_func(self): return self.request.user.is_student
    def post(self, request, *args, **kwargs):
        student_profile = request.user.studentprofile
        student_profile.phone_number = request.POST.get('phone_number', '').strip()
        student_profile.save()
        messages.success(request, "Details saved.")
        return redirect('student_dashboard')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_profile = self.request.user.studentprofile
        context['courses'] = student_profile.courses.all()
        context['grades'] = Grade.objects.filter(student=student_profile)
        context['activities'] = SchoolActivity.objects.all()[:3]
        avg_score = Grade.objects.filter(student=student_profile).aggregate(Avg('score'))['score__avg'] or 0.0
        context['academic_average'] = round(avg_score, 1)
        total_att = Attendance.objects.filter(student=student_profile).count()
        present_att = Attendance.objects.filter(student=student_profile, status='Present').count()
        context['attendance_rate'] = round((present_att / total_att) * 100, 1) if total_att > 0 else 100.0
        return context

class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/teacher_dashboard.html'
    def test_func(self): return self.request.user.is_teacher
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher_profile = self.request.user.teacherprofile
        assigned_courses = Course.objects.filter(teacher=teacher_profile)
        context['courses'] = assigned_courses
        context['activities'] = SchoolActivity.objects.all()[:3]
        return context

@login_required
def messages_view(request):
    messages_query = Message.objects.filter(sender=request.user) | Message.objects.filter(receiver=request.user)
    messages_query = messages_query.order_by('timestamp')
    recipients = User.objects.filter(is_student=True) if request.user.is_teacher else User.objects.filter(is_teacher=True)
    if request.method == "POST":
        receiver = User.objects.get(id=request.POST.get('receiver'))
        Message.objects.create(sender=request.user, receiver=receiver, content=request.POST.get('content'))
        return redirect('messages')
    return render(request, 'core/messages.html', {'chat_messages': messages_query, 'recipients': recipients})

@login_required
def analytics_view(request):
    if request.user.is_student:
        student = request.user.studentprofile
        grades_data = Grade.objects.filter(student=student)
        total_present = Attendance.objects.filter(student=student, status='Present').count()
        total_absent = Attendance.objects.filter(student=student, status='Absent').count()
        avg_score = grades_data.aggregate(Avg('score'))['score__avg'] or 0.0
        return render(request, 'core/analytics.html', {'is_student': True, 'grades_data': grades_data, 'total_present': total_present, 'total_absent': total_absent, 'avg_score': round(avg_score, 1)})
    else:
        students_data = StudentProfile.objects.annotate(avg_grade=Avg('grades__score')).order_by('-avg_grade')[:15]
        return render(request, 'core/analytics.html', {'is_student': False, 'students_data': students_data})

@login_required
def homework_hub_view(request):
    if request.user.is_student:
        assignments = Assignment.objects.all().order_by('-due_date')
        submissions = {s.assignment.id: s for s in AssignmentSubmission.objects.filter(student=request.user.studentprofile)}
        return render(request, 'core/homework_hub.html', {'is_student': True, 'assignments': assignments, 'submissions': submissions})
    else:
        teacher = request.user.teacherprofile
        my_courses = Course.objects.filter(teacher=teacher)
        my_assignments = Assignment.objects.filter(course__in=my_courses)
        pending_grading = AssignmentSubmission.objects.filter(assignment__course__in=my_courses, points_earned__isnull=True)
        if request.method == "POST":
            course = get_object_or_404(Course, id=request.POST.get('course'), teacher=teacher)
            Assignment.objects.create(course=course, title=request.POST.get('title'), instructions=request.POST.get('instructions'), due_date=request.POST.get('due_date'))
            return redirect('homework_hub')
        return render(request, 'core/homework_hub.html', {'is_student': False, 'courses': my_courses, 'assignments': my_assignments, 'pending_grading': pending_grading})


# --- AUTO-GENERATED PLACEHOLDERS ---
from django.http import HttpResponse
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
def student_detail_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for student_detail_view")

def student_directory_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for student_directory_view")

def student_drop_course_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for student_drop_course_view")

def student_enrollment_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for student_enrollment_view")

def student_fee_receipt_pdf(request, *args, **kwargs):
    return HttpResponse("Placeholder for student_fee_receipt_pdf")

def student_fees_pay_demo_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for student_fees_pay_demo_view")

def student_fees_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for student_fees_view")

def student_homework_receipt_pdf(request, *args, **kwargs):
    return HttpResponse("Placeholder for student_homework_receipt_pdf")

def student_report_card_pdf(request, *args, **kwargs):
    return HttpResponse("Placeholder for student_report_card_pdf")

def student_submit_homework_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for student_submit_homework_view")

def student_timetable_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for student_timetable_view")

def teacher_attendance_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for teacher_attendance_view")

def teacher_grade_homework_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for teacher_grade_homework_view")

def teacher_grades_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for teacher_grades_view")

def teacher_reenroll_student_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for teacher_reenroll_student_view")

def teacher_send_fee_reminder(request, *args, **kwargs):
    return HttpResponse("Placeholder for teacher_send_fee_reminder")

def teacher_suspend_student(request, *args, **kwargs):
    return HttpResponse("Placeholder for teacher_suspend_student")

def teacher_timetable_view(request, *args, **kwargs):
    return HttpResponse("Placeholder for teacher_timetable_view")

