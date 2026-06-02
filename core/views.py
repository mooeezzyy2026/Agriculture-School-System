import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.db.models import Avg
from .models import Course, Grade, Message, User, StudentProfile, Attendance, SchoolActivity

@login_required
def login_redirect_view(request):
    if request.user.is_student:
        return redirect('student_dashboard')
    elif request.user.is_teacher:
        return redirect('teacher_dashboard')
    else:
        return redirect('analytics')

class StudentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/student_dashboard.html'

    def test_func(self):
        return self.request.user.is_student

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_profile = self.request.user.studentprofile
        context['courses'] = student_profile.courses.all()
        context['grades'] = Grade.objects.filter(student=student_profile)
        context['activities'] = SchoolActivity.objects.all()[:3]
        return context

class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/teacher_dashboard.html'

    def test_func(self):
        return self.request.user.is_teacher

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher_profile = self.request.user.teacherprofile
        context['courses'] = Course.objects.filter(teacher=teacher_profile)
        context['activities'] = SchoolActivity.objects.all()[:3]
        return context

@login_required
def messages_view(request):
    messages = Message.objects.filter(sender=request.user) | Message.objects.filter(receiver=request.user)
    messages = messages.order_by('timestamp')

    if request.user.is_teacher:
        recipients = User.objects.filter(is_student=True)
    else:
        recipients = User.objects.filter(is_teacher=True)

    if request.method == "POST":
        receiver_id = request.POST.get('receiver')
        content = request.POST.get('content')
        if receiver_id and content:
            receiver = User.objects.get(id=receiver_id)
            Message.objects.create(sender=request.user, receiver=receiver, content=content)
            return redirect('messages')

    return render(request, 'core/messages.html', {
        'chat_messages': messages,
        'recipients': recipients
    })

@login_required
def analytics_view(request):
    students_data = StudentProfile.objects.annotate(
        avg_grade=Avg('grades__score')
    ).order_by('-avg_grade')[:15]

    total_present = Attendance.objects.filter(status='Present').count()
    total_absent = Attendance.objects.filter(status='Absent').count()

    return render(request, 'core/analytics.html', {
        'students_data': students_data,
        'total_present': total_present,
        'total_absent': total_absent,
    })

@login_required
def info_page_view(request, info_type):
    pages = {
        'school-history': {
            'title': 'School History',
            'content': 'Established in 1952 in Faisalabad, the Agriculture School has been a pioneer in modern agricultural education...',
            'details': [
                '1952: School founded by local agronomists.',
                '1975: Completed the Soil Quality Research Laboratory.',
                '1998: Built the main computer labs to study agri-tech statistics.',
                '2018: Installed smart organic greenhouses and hydroponic systems.'
            ]
        },
        'global-programs': {
            'title': 'Global Programs',
            'content': 'We partner with world-renowned agricultural universities across Australia, the Netherlands, and the USA...',
            'details': [
                'Exchange Semesters with Soil Research Institutes in Melbourne, Australia.',
                'Hydroponics and Floriculture Internships in Rotterdam, Netherlands.',
                'Collaborative research webinars with Agronomy departments in California, USA.'
            ]
        },
        'alumni-network': {
            'title': 'Alumni Network',
            'content': 'Our alumni network spans the globe, with graduates leading innovations in organic farming...',
            'details': [
                'Dr. Asif Chaudhry - Senior Agri-Tech Policy Advisor, United Nations.',
                'Sana Malik - Founder of Green Harvest Organics, Lahore.',
                'Bilal Shah - Lead Agronomist, Punjab Agricultural Department.'
            ]
        },
        'academic-calendar': {
            'title': 'Academic Calendar',
            'content': 'Keep track of crucial semester timelines, examinations, and agricultural festival vacations.',
            'details': [
                'September 10: Fall Semester Commencement.',
                'November 05: Mid-Term Examination Phase.',
                'March 15: Wheat Harvest Festival (National Holiday - Campus Closed).',
                'June 12: Final Examinations and Project Exhibition.'
            ]
        }
    }
    
    data = pages.get(info_type, {
        'title': 'Page Not Found',
        'content': 'The requested info page does not exist.',
        'details': []
    })
    
    return render(request, 'core/info_page.html', {'page': data})

# --- New Views for Phase 1 ---

# 1. Manage Grades View
@login_required
def teacher_grades_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user.teacherprofile)
    students = course.students.all()
    
    if request.method == "POST":
        for student in students:
            score = request.POST.get(f'grade_{student.id}')
            remarks = request.POST.get(f'remarks_{student.id}', '')
            if score:
                Grade.objects.update_or_create(
                    student=student,
                    course=course,
                    defaults={'score': score, 'remarks': remarks}
                )
        return redirect('teacher_dashboard')
    
    # Prepopulate with existing grades
    grades = {g.student.id: g for g in Grade.objects.filter(course=course)}
    
    return render(request, 'core/teacher_grades.html', {
        'course': course,
        'students': students,
        'grades': grades
    })

# 2. Mark Attendance View
@login_required
def teacher_attendance_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user.teacherprofile)
    students = course.students.all()
    
    # Get date from form or use today's date
    date_str = request.GET.get('date', str(datetime.date.today()))
    try:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        date = datetime.date.today()

    if request.method == "POST":
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'Absent')
            Attendance.objects.update_or_create(
                student=student,
                course=course,
                date=date,
                defaults={'status': status}
            )
        return redirect('teacher_dashboard')
        
    # Prepopulate existing attendance records
    attendance = {a.student.id: a.status for a in Attendance.objects.filter(course=course, date=date)}
    
    return render(request, 'core/teacher_attendance.html', {
        'course': course,
        'students': students,
        'date': str(date),
        'attendance': attendance
    })
