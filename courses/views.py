from django.shortcuts import render, get_object_or_404
from .models import MasterCategory, Course, Carousel, SuccessStory, StudyMaterial, YouTubeChannel

def home(request):
    context = {
        'categories': MasterCategory.objects.all().order_by('order'),
        'slides': Carousel.objects.filter(is_active=True),
        'popular_courses': Course.objects.filter(is_active=True).order_by('-enrollment_count')[:4],
        'new_courses': Course.objects.filter(is_active=True).order_by('-created_at')[:4],
        'success_stories': SuccessStory.objects.all()[:3],
        'study_materials': StudyMaterial.objects.all().order_by('order'),
        'youtube_channels': YouTubeChannel.objects.all(),
    }
    return render(request, 'courses/home.html', context)

def category_detail(request, slug):
    # Fetch the specific category or return 404 if not found
    category = get_object_or_404(MasterCategory, slug=slug)
    
    # Filter courses belonging to this category and are active
    courses = Course.objects.filter(master_category=category, is_active=True)
    
    context = {
        'category': category,
        'courses': courses,
    }
    return render(request, 'courses/category_detail.html', context)

def course_detail(request, slug):
    # Fetch the course by it's slug
    course = get_object_or_404(Course, slug=slug)

    # Fetch all modules belonging to this course, ordered by 'order'

    modules = course.modules.all().prefetch_related('lessons')

    context = {
        'course': course,
        'modules': modules,
    }

    return render(request, 'courses/course_detail.html', context)