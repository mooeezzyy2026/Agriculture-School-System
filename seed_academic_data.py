import os
import random
import datetime
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_system.settings')
django.setup()

from core.models import StudentProfile, TeacherProfile, Course, Grade, Attendance

# 8 Core Subjects
subjects = [
    ("Mathematics", "MATH101"),
    ("Physics", "PHY101"),
    ("Chemistry", "CHM101"),
    ("Biology", "BIO101"),
    ("English Lit", "ENG101"),
    ("Urdu Lit", "URD101"),
    ("Computer Science", "CS101"),
    ("Pakistan Studies", "PAK101")
]

def seed_academic_data():
    print("Beginning Academic Seeding...")
    
    # Fetch existing teachers and students
    teachers = list(TeacherProfile.objects.all())
    students = list(StudentProfile.objects.all())

    if not teachers or not students:
        print("Error: Run seed_data.py first to create teachers and students.")
        return

    # 1. Create the 8 Courses and assign random teachers
    print("Configuring 8 Core Courses...")
    course_objects = []
    for name, code in subjects:
        # Check if course already exists, otherwise create it
        course, created = Course.objects.get_or_create(
            code=code,
            defaults={'name': name, 'teacher': random.choice(teachers)}
        )
        if created:
            print(f"Created Course: {name} ({code})")
        course_objects.append(course)

    # 2. Enroll all students in all 8 courses, create random grades & attendance
    print("Enrolling all students and generating mock grades/attendance...")
    
    # Generate dates for 10 days of attendance
    today = datetime.date.today()
    dates = [today - datetime.timedelta(days=i) for i in range(10)]

    for student in students:
        for course in course_objects:
            # Enroll student in course
            course.students.add(student)

            # Generate random grades (between 50% and 100%)
            Grade.objects.get_or_create(
                student=student,
                course=course,
                defaults={'score': random.randint(50, 100), 'remarks': "Mock Grade"}
            )

            # Generate 10 days of random attendance records (85% attendance rate)
            for date in dates:
                status = 'Present' if random.random() < 0.85 else 'Absent'
                Attendance.objects.get_or_create(
                    student=student,
                    course=course,
                    date=date,
                    defaults={'status': status}
                )

    print("Success! Academic seeding completed cleanly.")

if __name__ == '__main__':
    seed_academic_data()
