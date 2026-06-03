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

    def post(self, request, *args, **kwargs):
        student_profile = request.user.studentprofile
        phone = request.POST.get('phone_number', '').strip()
        student_profile.phone_number = phone
        student_profile.save()
        messages.success(request, "Contact profile details saved successfully.")
        return redirect('student_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_profile = self.request.user.studentprofile
        context['courses'] = student_profile.courses.all()
        context['grades'] = Grade.objects.filter(student=student_profile)
        context['activities'] = SchoolActivity.objects.all()[:3]
        
        avg_score = Grade.objects.filter(student=student_profile).aggregate(Avg('score'))['score__avg']
        context['academic_average'] = round(avg_score, 1) if avg_score else 0.0
        
        total_att = Attendance.objects.filter(student=student_profile).count()
        present_att = Attendance.objects.filter(student=student_profile, status='Present').count()
        context['attendance_rate'] = round((present_att / total_att) * 100, 1) if total_att > 0 else 100.0
        return context

class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/teacher_dashboard.html'

    def test_func(self):
        return self.request.user.is_teacher

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher_profile = self.request.user.teacherprofile
        assigned_courses = Course.objects.filter(teacher=teacher_profile)
        context['courses'] = assigned_courses
        context['activities'] = SchoolActivity.objects.all()[:3]
        
        total_students = StudentProfile.objects.filter(courses__in=assigned_courses).distinct().count()
        context['total_students'] = total_students
        
        total_att = Attendance.objects.filter(course__in=assigned_courses).count()
        present_att = Attendance.objects.filter(course__in=assigned_courses, status='Present').count()
        context['class_attendance_avg'] = round((present_att / total_att) * 100, 1) if total_att > 0 else 100.0
        return context

@login_required
def messages_view(request):
    messages_query = Message.objects.filter(sender=request.user) | Message.objects.filter(receiver=request.user)
    messages_query = messages_query.order_by('timestamp')

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
        'chat_messages': messages_query,
        'recipients': recipients
    })

@login_required
def analytics_view(request):
    if request.user.is_student:
        student = request.user.studentprofile
        grades_data = Grade.objects.filter(student=student)
        total_present = Attendance.objects.filter(student=student, status='Present').count()
        total_absent = Attendance.objects.filter(student=student, status='Absent').count()
        
        return render(request, 'core/analytics.html', {
            'is_student': True,
            'grades_data': grades_data,
            'total_present': total_present,
            'total_absent': total_absent,
        })
    else:
        students_data = StudentProfile.objects.annotate(
            avg_grade=Avg('grades__score')
        ).order_by('-avg_grade')[:15]

        total_present = Attendance.objects.filter(status='Present').count()
        total_absent = Attendance.objects.filter(status='Absent').count()

        return render(request, 'core/analytics.html', {
            'is_student': False,
            'students_data': students_data,
            'total_present': total_present,
            'total_absent': total_absent,
        })

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
        messages.success(request, "Grades updated successfully.")
        return redirect('teacher_dashboard')
    
    grades = {g.student.id: g for g in Grade.objects.filter(course=course)}
    
    return render(request, 'core/teacher_grades.html', {
        'course': course,
        'students': students,
        'grades': grades
    })

@login_required
def teacher_attendance_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user.teacherprofile)
    students = course.students.all()
    
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
        messages.success(request, f"Attendance for {date} saved successfully.")
        return redirect('teacher_dashboard')
        
    attendance = {a.student.id: a.status for a in Attendance.objects.filter(course=course, date=date)}
    
    return render(request, 'core/teacher_attendance.html', {
        'course': course,
        'students': students,
        'date': str(date),
        'attendance': attendance
    })

@login_required
def student_report_card_pdf(request):
    if not request.user.is_student:
        return HttpResponse("Access Denied: Only students can generate report cards.", status=403)
        
    student = request.user.studentprofile
    grades = Grade.objects.filter(student=student)
    avg_score = grades.aggregate(Avg('score'))['score__avg'] or 0.0

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Report_Card_{student.roll_number}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    p.setFillColor(colors.HexColor('#064e3b'))
    p.rect(0, height - 90, width, 90, fill=True, stroke=False)

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(40, height - 45, "AGRICULTURE SCHOOL SYSTEM")
    p.setFont("Helvetica", 10)
    p.drawString(40, height - 65, "Official Transcript & Academic Progress Statement")

    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, height - 130, f"Student: {request.user.get_full_name() or request.user.username}")
    p.drawString(40, height - 150, f"Roll Number: {student.roll_number}")
    p.drawString(40, height - 170, f"Class Name: {student.class_name}")
    p.drawString(40, height - 190, f"Cumulative Avg: {round(avg_score, 1)}%")

    p.setStrokeColor(colors.HexColor('#94a3b8'))
    p.line(40, height - 215, width - 40, height - 215)

    p.setFont("Helvetica-Bold", 10)
    p.drawString(40, height - 230, "Subject Code")
    p.drawString(150, height - 230, "Subject Name")
    p.drawString(350, height - 230, "Grade Score %")
    p.drawString(450, height - 230, "Instructor Remarks")
    p.line(40, height - 240, width - 40, height - 240)

    p.setFont("Helvetica", 10)
    y = height - 260
    for grade in grades:
        p.drawString(40, y, grade.course.code)
        p.drawString(150, y, grade.course.name)
        p.drawString(350, y, f"{grade.score}%")
        p.drawString(450, y, grade.remarks or "-")
        y -= 25

    p.line(40, y + 15, width - 40, y + 15)

    p.setFont("Helvetica-Bold", 10)
    p.drawString(40, 80, "Principal's Signature: _______________________")
    p.drawString(380, 80, "Date: ____________________")

    p.showPage()
    p.save()
    return response

@login_required
def student_enrollment_view(request):
    if not request.user.is_student:
        return redirect('login_redirect')
        
    student = request.user.studentprofile
    all_courses = Course.objects.all()
    enrolled_courses = student.courses.all()

    if request.method == "POST":
        selected_course_ids = request.POST.getlist('courses')
        count = len(selected_course_ids)
        
        if 8 <= count <= 10:
            student.courses.clear()
            for c_id in selected_course_ids:
                course = Course.objects.get(id=c_id)
                course.students.add(student)
            messages.success(request, f"Subjects updated successfully. You are enrolled in {count} subjects.")
            return redirect('student_dashboard')
        else:
            error_msg = f"Selection failed: You must select a minimum of 8 and a maximum of 10 subjects. You selected {count}."
            return render(request, 'core/student_enrollment.html', {
                'courses': all_courses,
                'enrolled_courses': enrolled_courses,
                'error': error_msg
            })

    return render(request, 'core/student_enrollment.html', {
        'courses': all_courses,
        'enrolled_courses': enrolled_courses
    })

@login_required
def student_timetable_view(request):
    if not request.user.is_student:
        return redirect('login_redirect')
    
    student_profile = request.user.studentprofile
    courses = student_profile.courses.all()
    return render(request, 'core/student_timetable.html', {'courses': courses})

@login_required
def student_drop_course_view(request, course_id):
    if not request.user.is_student:
        return redirect('login_redirect')
        
    student = request.user.studentprofile
    course = get_object_or_404(Course, id=course_id)
    
    current_count = student.courses.count()
    if current_count <= 8:
        messages.error(request, "Drop failed: You cannot drop this course. You must stay enrolled in at least 8 subjects.")
    else:
        course.students.remove(student)
        messages.success(request, f"Successfully dropped {course.code} - {course.name}.")
        
    return redirect('student_dashboard')

# --- NEW VIEWS FOR THE TEACHER STUDENT DIRECTORY & DETAILS ---

# 1. Student Directory View (Teacher only)
@login_required
def student_directory_view(request):
    if not request.user.is_teacher:
        return redirect('login_redirect')
    students = StudentProfile.objects.all().order_by('roll_number')
    return render(request, 'core/student_directory.html', {'students': students})

# 2. Student Detail Profile View (Teacher only)
@login_required
def student_detail_view(request, student_id):
    if not request.user.is_teacher:
        return redirect('login_redirect')
        
    student = get_object_or_404(StudentProfile, id=student_id)
    grades = Grade.objects.filter(student=student)
    
    # Calculate Academic Stats
    avg_score = grades.aggregate(Avg('score'))['score__avg'] or 0.0
    
    # Calculate Attendance Stats
    total_att = Attendance.objects.filter(student=student).count()
    present_att = Attendance.objects.filter(student=student, status='Present').count()
    absent_att = total_att - present_att
    attendance_rate = round((present_att / total_att) * 100, 1) if total_att > 0 else 100.0

    # Calculate Academic Capability Rating
    if avg_score >= 90:
        capability = "Outstanding (A+)"
    elif avg_score >= 80:
        capability = "Excellent (A)"
    elif avg_score >= 70:
        capability = "Good (B)"
    elif avg_score >= 50:
        capability = "Satisfactory (C)"
    else:
        capability = "Needs Improvement (F)"

    return render(request, 'core/student_detail.html', {
        'student': student,
        'grades': grades,
        'avg_score': round(avg_score, 1),
        'attendance_rate': attendance_rate,
        'total_present': present_att,
        'total_absent': absent_att,
        'capability': capability
    })
