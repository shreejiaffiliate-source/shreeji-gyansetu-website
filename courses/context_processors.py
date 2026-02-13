from .models import MasterCategory

def extras(request):
    # This logic limits the display to exactly 4 categories as requested
    return {
        'all_categories': MasterCategory.objects.all().order_by('order')[:4]
    }