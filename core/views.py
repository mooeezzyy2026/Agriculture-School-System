import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, Assignment, AssignmentSubmission, StudentProfile, TeacherProfile, SchoolActivity, Grade, Message, Attendance, FeeRecord, ResearchLog

@login_required
def homework_hub_view(request):
    if request.user.is_student:
        student = request.user.studentprofile
        assignments = Assignment.objects.all().order_by('-due_date')
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
                    course=course, title=title, instructions=instructions, 
                    due_date=due_date, max_points=max_points
                )
                messages.success(request, f"Homework Notice '{title}' published.")
                return redirect('homework_hub')
                
        return render(request, 'core/homework_hub.html', {
            'is_student': False,
            'courses': my_courses,
            'assignments': my_assignments,
            'pending_grading': pending_grading
        })
