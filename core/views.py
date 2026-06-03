import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.db.models import Avg
from django.http import HttpResponse
from django.contrib import messages

# PDF generation imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

from .models import Course, Grade, Message, User, StudentProfile, Attendance, SchoolActivity, FeeRecord, Assignment, AssignmentSubmission

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
        
        highest_achievers = []
        for course in student.courses.all():
            top_grade = Grade.objects.filter(course=course).order_by('-score').first()
            if top_grade:
                highest_achievers.append({
                    'course_code': course.code,
                    'course_name': course.name,
                    'student_name': top_grade.student.user.get_full_name() or top_grade.student.user.username,
                    'score': top_grade.score
                })
        
        return render(request, 'core/analytics.html', {
            'is_student': True,
            'grades_data': grades_data,
            'total_present': total_present,
            'total_absent': total_absent,
            'highest_achievers': highest_achievers
        })
    else:
        students_data = StudentProfile.objects.annotate(
            avg_grade=Avg('grades__score')
        ).order_by('-avg_grade')[:15]

        if request.user.is_teacher:
            teacher_profile = request.user.teacherprofile
            assigned_courses = Course.objects.filter(teacher=teacher_profile)
            total_present = Attendance.objects.filter(course__in=assigned_courses, status='Present').count()
            total_absent = Attendance.objects.filter(course__in=assigned_courses, status='Absent').count()
            
            highest_achievers = []
            for course in assigned_courses:
                top_grade = Grade.objects.filter(course=course).order_by('-score').first()
                if top_grade:
                    highest_achievers.append({
                        'course_code': course.code,
                        'course_name': course.name,
                        'student_name': top_grade.student.user.get_full_name() or top_grade.student.user.username,
                        'score': top_grade.score
                    })
        else:
            total_present = Attendance.objects.filter(status='Present').count()
            total_absent = Attendance.objects.filter(status='Absent').count()
            highest_achievers = []

        return render(request, 'core/analytics.html', {
            'is_student': False,
            'students_data': students_data,
            'total_present': total_present,
            'total_absent': total_absent,
            'highest_achievers': highest_achievers
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

@login_required
def student_directory_view(request):
    if not request.user.is_teacher:
        return redirect('login_redirect')
    students = StudentProfile.objects.all().order_by('roll_number')
    return render(request, 'core/student_directory.html', {'students': students})

@login_required
def student_detail_view(request, student_id):
    if not request.user.is_teacher:
        return redirect('login_redirect')
        
    student = get_object_or_404(StudentProfile, id=student_id)
    grades = Grade.objects.filter(student=student)
    
    avg_score = grades.aggregate(Avg('score'))['score__avg'] or 0.0
    
    total_att = Attendance.objects.filter(student=student).count()
    present_att = Attendance.objects.filter(student=student, status='Present').count()
    absent_att = total_att - present_att
    attendance_rate = round((present_att / total_att) * 100, 1) if total_att > 0 else 100.0

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

@login_required
def teacher_timetable_view(request):
    if not request.user.is_teacher:
        return redirect('login_redirect')
    
    teacher_profile = request.user.teacherprofile
    courses = Course.objects.filter(teacher=teacher_profile)
    return render(request, 'core/teacher_timetable.html', {'courses': courses})

@login_required
def student_fees_view(request):
    if not request.user.is_student:
        return redirect('login_redirect')
    student = request.user.studentprofile
    fee_record, created = FeeRecord.objects.get_or_create(student=student)
    return render(request, 'core/student_fees.html', {
        'fee_record': fee_record,
    })

@login_required
def student_fee_receipt_pdf(request):
    if not request.user.is_student:
        return HttpResponse("Access Denied.", status=403)
        
    student = request.user.studentprofile
    fee_record = get_object_or_404(FeeRecord, student=student)
    
    if fee_record.status != 'Paid':
        return HttpResponse("Error: You can only download receipts for fully Paid fee records.", status=400)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Fee_Receipt_{student.roll_number}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    p.setFillColor(colors.HexColor('#064e3b'))
    p.rect(0, height - 90, width, 90, fill=True, stroke=False)

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(40, height - 45, "AGRICULTURE SCHOOL SYSTEM")
    p.setFont("Helvetica", 10)
    p.drawString(40, height - 65, "Official Payment Receipt - Fee & Institutional Dues")

    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, height - 130, f"Student: {request.user.get_full_name() or request.user.username}")
    p.drawString(40, height - 150, f"Roll Number: {student.roll_number}")
    p.drawString(40, height - 170, f"Status: {fee_record.status} (Verified)")

    p.setStrokeColor(colors.HexColor('#cbd5e1'))
    p.line(40, height - 200, width - 40, height - 200)

    p.setFont("Helvetica-Bold", 10)
    p.drawString(40, height - 215, "Fee Head Description")
    p.drawString(450, height - 215, "Amount (PKR)")
    p.line(40, height - 225, width - 40, height - 225)

    p.setFont("Helvetica", 10)
    p.drawString(40, height - 245, "Tuition Fees (Semester Base)")
    p.drawString(450, height - 245, f"PKR {fee_record.tuition_fee}")

    p.drawString(40, height - 270, "Library Institutional Dues")
    p.drawString(450, height - 270, f"PKR {fee_record.library_dues}")

    p.drawString(40, height - 295, "Agricultural Science Lab Dues")
    p.drawString(450, height - 295, f"PKR {fee_record.lab_dues}")

    p.line(40, height - 310, width - 40, height - 310)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, height - 325, "Total Verified Dues Paid:")
    p.drawString(450, height - 325, f"PKR {fee_record.total_amount}")
    p.line(40, height - 335, width - 40, height - 335)

    p.setFont("Helvetica-Bold", 10)
    p.drawString(40, 80, "Accounts Officer Signature: _______________________")
    p.drawString(380, 80, f"Date Paid: {fee_record.updated_at.date()}")

    p.showPage()
    p.save()
    return response

@login_required
def teacher_send_fee_reminder(request, student_id):
    if not request.user.is_teacher:
        return redirect('login_redirect')
        
    student = get_object_or_404(StudentProfile, id=student_id)
    fee_record = get_object_or_404(FeeRecord, student=student)
    
    if fee_record.status == 'Paid':
        messages.error(request, "Reminder failed: This student has already cleared all dues.")
        return redirect('student_detail', student_id=student.id)

    reminder_content = f"AUTOMATED FEE WARNING: Dear {student.user.get_full_name() or student.user.username}, this is an official reminder to clear your outstanding institutional dues of PKR {fee_record.total_amount} immediately to prevent suspension of your portal account access."
    
    Message.objects.create(
        sender=request.user,
        receiver=student.user,
        content=reminder_content
    )
    
    messages.success(request, f"Fee Warning Reminder sent successfully to {student.user.username} via Direct Messages.")
    return redirect('student_detail', student_id=student.id)

@login_required
def teacher_suspend_student(request, student_id):
    if not request.user.is_teacher:
        return redirect('login_redirect')
        
    student = get_object_or_404(StudentProfile, id=student_id)
    user = student.user
    
    if user.is_active:
        user.is_active = False
        user.save()
        messages.success(request, f"Student Account {user.username} has been SUSPENDED from school due to unpaid dues.")
    else:
        user.is_active = True
        user.save()
        messages.success(request, f"Student Account {user.username} has been REINSTATED successfully. Portal access restored.")
        
    return redirect('student_detail', student_id=student.id)

@login_required
def student_fees_pay_demo_view(request):
    if not request.user.is_student:
        return redirect('login_redirect')
    student = request.user.studentprofile
    fee_record = get_object_or_404(FeeRecord, student=student)
    
    if request.method == "POST":
        card_number = request.POST.get('card_number', '').strip()
        card_brand = request.POST.get('card_brand', '')
        
        if card_number and card_brand:
            fee_record.status = 'Paid'
            fee_record.save()
            safe_card = f"**** **** **** {card_number[-4:]}" if len(card_number) >= 4 else "****"
            messages.success(request, f"Payment authorized successfully via {card_brand} ({safe_card})! Your outstanding dues of PKR {fee_record.total_amount} have been cleared.")
        else:
            messages.error(request, "Payment failed: Please fill out all required secure checkout fields.")
            
    return redirect('student_fees')

@login_required
def teacher_reenroll_student_view(request, student_id):
    if not request.user.is_teacher:
        return redirect('login_redirect')
    student = get_object_or_404(StudentProfile, id=student_id)
    fee_record = get_object_or_404(FeeRecord, student=student)
    
    if request.method == "POST":
        fee_record.status = 'Paid'
        fee_record.save()
        student.user.is_active = True
        student.user.save()
        messages.success(request, f"Dues cleared! Student {student.user.get_full_name() or student.user.username} has been reinstated and re-enrolled into classes successfully.")
    return redirect('student_detail', student_id=student.id)

# --- HOMEWORK HUB VIEWS ---

@login_required
def homework_hub_view(request):
    if request.user.is_student:
        student = request.user.studentprofile
        enrolled_courses = student.courses.all()
        assignments = Assignment.objects.filter(course__in=enrolled_courses).order_by('-due_date')
        submissions = {s.assignment.id: s for s in AssignmentSubmission.objects.filter(student=student)}
        
        return render(request, 'core/homework_hub.html', {
            'is_student': True,
            'assignments': assignments,
            'submissions': submissions
        })
    else:
        teacher = request.user.teacherprofile
        my_courses = Course.objects.filter(teacher=teacher)
        my_assignments = Assignment.objects.filter(course__in=my_courses).order_by('-due_date')
        pending_grading = AssignmentSubmission.objects.filter(assignment__course__in=my_courses, points_earned__isnull=True).order_by('submitted_at')
        
        if request.method == "POST":
            course_id = request.POST.get('course')
            title = request.POST.get('title')
            instructions = request.POST.get('instructions')
            due_date_str = request.POST.get('due_date')
            max_points = request.POST.get('max_points', 100)
            
            if course_id and title and instructions and due_date_str:
                course = get_object_or_404(Course, id=course_id, teacher=teacher)
                due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
                Assignment.objects.create(
                    course=course,
                    title=title,
                    instructions=instructions,
                    due_date=due_date,
                    max_points=max_points
                )
                messages.success(request, f"Homework Notice '{title}' has been published successfully.")
                return redirect('homework_hub')
                
        return render(request, 'core/homework_hub.html', {
            'is_student': False,
            'courses': my_courses,
            'assignments': my_assignments,
            'pending_grading': pending_grading
        })

@login_required
def student_submit_homework_view(request, assignment_id):
    if not request.user.is_student:
        return redirect('login_redirect')
        
    student = request.user.studentprofile
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    existing_sub = AssignmentSubmission.objects.filter(assignment=assignment, student=student).first()
    if existing_sub:
        messages.error(request, "Error: You have already submitted homework for this assignment.")
        return redirect('homework_hub')

    if request.method == "POST":
        sub_text = request.POST.get('submission_text')
        if sub_text:
            AssignmentSubmission.objects.create(
                assignment=assignment,
                student=student,
                submission_text=sub_text
            )
            messages.success(request, f"Homework for '{assignment.title}' submitted successfully.")
            return redirect('homework_hub')

    return render(request, 'core/homework_submit.html', {
        'assignment': assignment
    })

@login_required
def teacher_grade_homework_view(request, submission_id):
    if not request.user.is_teacher:
        return redirect('login_redirect')
        
    teacher = request.user.teacherprofile
    submission = get_object_or_404(AssignmentSubmission, id=submission_id, assignment__course__teacher=teacher)

    if request.method == "POST":
        points = request.POST.get('points_earned')
        feedback = request.POST.get('feedback', '')
        
        if points:
            submission.points_earned = int(points)
            submission.feedback = feedback
            submission.save()
            messages.success(request, f"Graded successfully. {submission.student.user.username} earned {points} marks.")
            return redirect('homework_hub')

    return render(request, 'core/homework_grade.html', {
        'sub': submission
    })
