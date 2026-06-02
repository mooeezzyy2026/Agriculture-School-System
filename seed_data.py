import os
import random
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import StudentProfile, TeacherProfile

User = get_user_model()

# Lists of Pakistani first names and last names to generate combinations
first_names_male = ["Muhammad", "Ahmed", "Ali", "Hamza", "Bilal", "Usman", "Zain", "Omer", "Faisal", "Junaid", "Asif", "Haris", "Arsalan", "Tariq", "Imran", "Nabeel", "Saad", "Yasir", "Waqas", "Adeel"]
first_names_female = ["Aisha", "Fatima", "Zainab", "Sana", "Mariam", "Anum", "Hira", "Amna", "Sidra", "Kiran", "Nida", "Saba", "Areeba", "Mahnoor", "Iqra", "Tayyaba", "Bushra", "Sajal", "Sadia", "Khadija"]
last_names = ["Khan", "Ahmed", "Ali", "Malik", "Shah", "Siddiqui", "Butt", "Iqbal", "Sheikh", "Chaudhry", "Raza", "Hussain", "Qureshi", "Latif", "Abbasi", "Dar", "Hashmi", "Gill", "Zaidi", "Mughal"]

subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Urdu", "Computer Science", "Pakistan Studies", "Islamic Studies"]
classes = ["Grade 9", "Grade 10", "Grade 11", "Grade 12"]

# Unified password for all generated users
TEST_PASSWORD = "Pak123Password!"

def create_users():
    print("Seeding database...")
    
    # 1. Create 30 Teachers
    print("Generating 30 Teachers...")
    for i in range(1, 31):
        gender = random.choice(['M', 'F'])
        first = random.choice(first_names_male) if gender == 'M' else random.choice(first_names_female)
        last = random.choice(last_names)
        full_name = f"{first} {last}"
        username = f"teacher_{first.lower()}{i}"
        
        # Avoid duplicate usernames
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                first_name=first,
                last_name=last,
                is_teacher=True
            )
            user.set_password(TEST_PASSWORD)
            user.save()
            
            TeacherProfile.objects.create(
                user=user,
                subject_specialty=random.choice(subjects),
                phone_number=f"0300{random.randint(1000000, 9999999)}"
            )

    # 2. Create 50 Students
    print("Generating 50 Students...")
    for i in range(1, 51):
        gender = random.choice(['M', 'F'])
        first = random.choice(first_names_male) if gender == 'M' else random.choice(first_names_female)
        last = random.choice(last_names)
        full_name = f"{first} {last}"
        username = f"student_{first.lower()}{i}"
        
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                first_name=first,
                last_name=last,
                is_student=True
            )
            user.set_password(TEST_PASSWORD)
            user.save()
            
            StudentProfile.objects.create(
                user=user,
                roll_number=f"2024-PK-{1000 + i}",
                class_name=random.choice(classes)
            )
            
    print(f"Success! Accounts generated. Default password is: {TEST_PASSWORD}")

if __name__ == '__main__':
    create_users()
