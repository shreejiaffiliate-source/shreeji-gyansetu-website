# Save this as repair_modules.py
import os
import django

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from courses.models import Module, Course, MasterCategory

def repair_modules():
    print("--- Starting Module Repair ---")
    
    # Fetch all modules that are missing a Master Category
    modules = Module.objects.filter(master_category__isnull=True)
    count = 0
    
    for mod in modules:
        # Look at the course this module belongs to
        if mod.course and mod.course.master_category:
            mod.master_category = mod.course.master_category
            mod.save()
            count += 1
            print(f"Fixed Module: '{mod.title}' -> Linked to Category: '{mod.master_category.title}'")
    
    print(f"--- Repair Complete: {count} modules restored ---")

if __name__ == '__main__':
    repair_modules()