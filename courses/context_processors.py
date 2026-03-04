from .models import MasterCategory, Notification

def extras(request):
    # This logic limits the display to exactly 4 categories as requested
    return {
        'all_categories': MasterCategory.objects.all().order_by('order')[:4]
    }

def unread_notifications(request):
    if request.user.is_authenticated:
        # Fetch count of unread notifications for the current user
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_count': count}
    return {'unread_count': 0}