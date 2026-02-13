# Save this as repair_lessons.py
import os
import django
import sqlite3

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') # Update with your project name
django.setup()

from courses.models import Lesson, Module

def repair():
    print("Starting lesson repair...")
    lessons = Lesson.objects.filter(course__isnull=True)
    count = 0
    
    for lesson in lessons:
        if lesson.module and lesson.module.course:
            lesson.course = lesson.module.course
            lesson.save()
            count += 1
            print(f"Fixed: {lesson.title} -> Assigned to {lesson.course.title}")
            
    print(f"Success! {count} lessons were repaired and are now linked to their courses.")

if __name__ == '__main__':
    repair()