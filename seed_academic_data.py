import os
import random
import datetime
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_system.settings')
django.setup()

from core.models import StudentProfile, TeacherProfile, Course, Grade, Attendance

# 15 Total Subjects (8 original + 7 brand new agricultural subjects)
subjects = [
    ("Mathematics", "MATH101"),
    ("Physics", "PHY101"),
    ("Chemistry", "CHM101"),
    ("Biology", "BIO101"),
    ("English Lit", "ENG101"),
    ("Urdu Lit", "URD101"),
    ("Computer Science", "CS101"),
    ("Pakistan Studies", "PAK101"),
    # New subjects:
    ("Agronomy & Crop Management", "AGR101"),
    ("Soil Science & Chemistry", "SOIL101"),
    ("Horticulture & Landscaping", "HORT101"),
    ("Entomology & Pest Control", "ENTO101"),
    ("Forestry & Silviculture", "FOR101"),
    ("Plant Pathology", "PATH101"),
    ("Agricultural Economics", "AGEC101")
]

def seed_academic_data():
    print("Resetting old academic records...")
    # Clear existing courses, grades, and attendance to prevent duplicate code errors
    Course.objects.all().delete()
    Grade.objects.all().delete()
    Attendance.objects.all().delete()

    # Fetch all teachers and students
    teachers = list(TeacherProfile.objects.all())
    students = list(StudentProfile.objects.all())

    if len(teachers) < 30:
        print("Error: Make sure you have all 30 teachers generated in your database first.")
        return

    print("Generating 30 unique course sections and assigning all 30 teachers...")
    course_sections = []
    teacher_index = 0

    # For each of the 15 subjects, create Section A and Section B
    for name, base_code in subjects:
        for section in ['A', 'B']:
            code = f"{base_code}-{section}"
            assigned_teacher = teachers[teacher_index]
            
            course = Course.objects.create(
                name=f"{name} (Section {section})",
                code=code,
                teacher=assigned_teacher
            )
            course_sections.append(course)
            teacher_index += 1

    print(f"Success! Created {len(course_sections)} courses. All 30 teachers assigned.")

    # Enroll students in exactly 8 random sections out of the 30 available
    print("Enrolling students in 8 random sections & generating grades/attendance...")
    
    today = datetime.date.today()
    dates = [today - datetime.timedelta(days=i) for i in range(10)]

    for student in students:
        # Select 8 random courses for this student
        selected_courses = random.sample(course_sections, 8)
        for course in selected_courses:
            course.students.add(student)

            # Create grades (between 50% and 100%)
            Grade.objects.create(
                student=student,
                course=course,
                score=random.randint(50, 100),
                remarks="Academic Evaluation"
            )

            # Create 10 days of attendance
            for date in dates:
                status = 'Present' if random.random() < 0.88 else 'Absent'
                Attendance.objects.create(
                    student=student,
                    course=course,
                    date=date,
                    status=status
                )

    print("Academic database successfully updated.")

if __name__ == '__main__':
    seed_academic_data()
