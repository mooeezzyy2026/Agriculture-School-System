import os
import random
import datetime
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_system.settings')
django.setup()

from core.models import StudentProfile, TeacherProfile, Course, Grade, Attendance

# 15 Total Subjects
subjects = [
    ("Mathematics", "MATH101"),
    ("Physics", "PHY101"),
    ("Chemistry", "CHM101"),
    ("Biology", "BIO101"),
    ("English Lit", "ENG101"),
    ("Urdu Lit", "URD101"),
    ("Computer Science", "CS101"),
    ("Pakistan Studies", "PAK101"),
    ("Agronomy & Crop Management", "AGR101"),
    ("Soil Science & Chemistry", "SOIL101"),
    ("Horticulture & Landscaping", "HORT101"),
    ("Entomology & Pest Control", "ENTO101"),
    ("Forestry & Silviculture", "FOR101"),
    ("Plant Pathology", "PATH101"),
    ("Agricultural Economics", "AGEC101")
]

# 5 Days of the Week
days_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

# 6 Daily Time Slots
slots = [
    (datetime.time(8, 30), datetime.time(10, 0)),
    (datetime.time(10, 15), datetime.time(11, 45)),
    (datetime.time(12, 0), datetime.time(13, 30)),
    (datetime.time(14, 0), datetime.time(15, 30)),
    (datetime.time(15, 45), datetime.time(17, 15)),
    (datetime.time(17, 30), datetime.time(19, 0))
]

def seed_academic_data():
    print("Resetting old academic records...")
    Course.objects.all().delete()
    Grade.objects.all().delete()
    Attendance.objects.all().delete()

    teachers = list(TeacherProfile.objects.all())
    students = list(StudentProfile.objects.all())

    if len(teachers) < 30:
        print("Error: Make sure you have all 30 teachers generated first.")
        return

    # Generate 30 unique day-time slots and SHUFFLE them randomly
    print("Generating and shuffling 30 unique timetable slots randomly...")
    all_slots = []
    for day in days_list:
        for start, end in slots:
            all_slots.append((day, start, end))
            
    random.shuffle(all_slots) # Randomized Shuffling

    print("Generating 30 unique course sections, scheduling days and times...")
    course_sections = []
    teacher_index = 0

    for name, base_code in subjects:
        for section in ['A', 'B']:
            code = f"{base_code}-{section}"
            assigned_teacher = teachers[teacher_index]
            
            # Map index (0-29) to shuffled day and timeslot
            day, start, end = all_slots[teacher_index]
            
            course = Course.objects.create(
                name=f"{name} (Section {section})",
                code=code,
                teacher=assigned_teacher,
                day_of_week=day,
                start_time=start,
                end_time=end
            )
            course_sections.append(course)
            teacher_index += 1

    print("Success! Created 30 courses with randomized schedules.")

    print("Enrolling students in 8 random sections & generating grades/attendance...")
    today = datetime.date.today()
    dates = [today - datetime.timedelta(days=i) for i in range(10)]

    for student in students:
        selected_courses = random.sample(course_sections, 8)
        for course in selected_courses:
            course.students.add(student)

            Grade.objects.create(
                student=student,
                course=course,
                score=random.randint(50, 100),
                remarks="Academic Evaluation"
            )

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
