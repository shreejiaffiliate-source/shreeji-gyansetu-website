# Save as master_repair.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from courses.models import Lesson, Module, Course

def run_repair():
    print("--- Starting Master Repair ---")

    # 1. Fix Module -> MasterCategory links
    modules = Module.objects.filter(master_category__isnull=True)
    for m in modules:
        if m.course and m.course.master_category:
            m.master_category = m.course.master_category
            m.save()
            print(f"Fixed Module: {m.title}")

    # 2. Fix Lesson -> Course links
    lessons = Lesson.objects.filter(course__isnull=True)
    for l in lessons:
        if l.module and l.module.course:
            l.course = l.module.course
            l.save()
            print(f"Fixed Lesson: {l.title}")

    print("--- Repair Complete ---")

if __name__ == '__main__':
    run_repair()