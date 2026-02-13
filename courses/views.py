from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden
from .models import MasterCategory, Course, Lesson, Carousel, SuccessStory, StudyMaterial, YouTubeChannel
from django.db.models import Q
from django.contrib.auth.decorators import login_required

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

def lesson_detail(request, course_slug, lesson_id):
    # Fetch the lesson and ensure it belongs to the correct course
    lesson = get_object_or_404(Lesson, id=lesson_id, course__slug=course_slug)
    
    # Simple Security: Only allow access if it's a preview
    # In the future, you can add: or request.user.has_purchased_course
    if not lesson.is_preview:
        return HttpResponseForbidden("This lesson is only available for enrolled students.")
    
    context = {
        'lesson': lesson,
        'course': lesson.course
    }
    return render(request, 'courses/lesson_player.html', context)

def search(request):
    query = request.GET.get('q')
    results = []
    if query:
        # Searches for the query in the title OR description
        results = Course.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            is_active=True
        )
    
    context = {
        'results': results,
        'query': query
    }
    return render(request, 'courses/search_results.html', context)


@login_required
def teacher_dashboard(request):
    if request.user.profile.user_type != 'Teacher':
        return HttpResponseForbidden("Access Dennied: Teachers Only")
    
    # Fetch courses belonging to this teacher
    my_course = Course.objects.filter(teacher=request.user)

    # Calculate some stats
    total_courses = my_course.count()
    total_enrollments = sum(Course.enrollment_count for course in my_course)

    context = {
        'my_course': my_course,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments
    }
    return render(request, 'courses/teacher_dashboard.html', context)