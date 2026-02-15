from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import MasterCategory, Course, Lesson, Carousel, SuccessStory, StudyMaterial, YouTubeChannel, Module, Profile
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .forms import CourseUploadForm, RegistrationForm, ModuleFormSet
from django.contrib.auth import login

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
    category = get_object_or_404(MasterCategory, slug=slug)
    courses = Course.objects.filter(master_category=category, is_active=True)
    return render(request, 'courses/category_detail.html', {'category': category, 'courses': courses})

def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    modules = course.modules.all().prefetch_related('lessons')
    return render(request, 'courses/course_detail.html', {'course': course, 'modules': modules})

def lesson_detail(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Check if student is enrolled or if it's a free preview
    user_is_enrolled = request.user.is_authenticated and request.user in course.students.all()
    
    if not (lesson.is_preview or user_is_enrolled):
        return HttpResponseForbidden("This lesson is locked. Please enroll in the course to view it.")
        

    # Fetch all modules and lessons for the sidebar navigation
    modules = course.modules.all().prefetch_related('lessons')

    context = {
        'course': course,
        'lesson': lesson,
        'modules': modules,
    }
    return render(request, 'courses/lesson_player.html', context)

def search(request):
    query = request.GET.get('q')
    results = Course.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        is_active=True
    ) if query else []
    return render(request, 'courses/search_results.html', {'results': results, 'query': query})

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            profile, created = Profile.objects.get_or_create(user=user)
            profile.user_type = form.cleaned_data['user_type']
            profile.save()
            login(request, user)
            return redirect('login_success')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def teacher_dashboard(request):
    if request.user.profile.user_type != 'Teacher':
        return HttpResponseForbidden("Access Denied: Teachers Only")
    
    my_courses = Course.objects.filter(teacher=request.user)
    total_courses = my_courses.count()
    total_enrollments = sum(course.enrollment_count for course in my_courses)

    context = {
        'my_course': my_courses,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments
    }
    return render(request, 'courses/teacher_dashboard.html', context)

@login_required
def upload_course(request):
    if request.user.profile.user_type != 'Teacher':
        return HttpResponseForbidden("Access Denied")
    
    if request.method == 'POST':
        form = CourseUploadForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            return redirect('teacher_dashboard')
    else:
        form = CourseUploadForm() # Corrected: Removed request.POST/FILES from GET request

    return render(request, 'courses/upload_course.html', {'form': form})
    
@login_required
def manage_curriculum(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug, teacher=request.user)
    if request.method == 'POST':
        formset = ModuleFormSet(request.POST, instance=course)
        if formset.is_valid():
            modules = formset.save(commit=False)
            for module in modules:
                module.master_category = course.master_category
                module.save()
            formset.save_m2m()
            return redirect('teacher_dashboard')
    else:
        formset = ModuleFormSet(instance=course)
    return render(request, 'courses/manage_curriculum.html', {'course': course, 'formset': formset})

@login_required
def add_lesson(request, module_id):
    module = get_object_or_404(Module, id=module_id, course__teacher=request.user)
    if request.method == 'POST':
        Lesson.objects.create(
            module=module,
            course=module.course,
            title=request.POST.get('title'),
            lesson_type=request.POST.get('lesson_type'),
            video_url=request.POST.get('video_url'),
            content_file=request.FILES.get('content_file'),
            is_preview=request.POST.get('is_preview') == 'on',
            lecturer_name=request.user.get_full_name()
        )
        return redirect('manage_curriculum', course_slug=module.course.slug)
    return render(request, 'courses/add_lesson.html', {'module': module})

@login_required
def login_success(request):
    if not hasattr(request.user, 'profile'):
        if request.user.is_superuser:
            return redirect('/admin/')
        return redirect('home')

    if request.user.profile.user_type == 'Teacher':
        return redirect('teacher_dashboard')
    elif request.user.profile.user_type == 'Admin':
        return redirect('/admin/')
    return redirect('home')

@login_required
def course_detail_edit(request, slug):
    course = get_object_or_404(Course, slug=slug, teacher=request.user)
    modules = course.modules.all().prefetch_related('lessons')
    context = {
        'course': course,
        'modules': modules,
        'is_edit_mode': True
    }
    return render(request, 'courses/course_detail_edit.html', context)

@login_required
def edit_course(request, slug):
    course = get_object_or_404(Course, slug=slug, teacher=request.user)
    if request.method == 'POST':
        form = CourseUploadForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_detail_edit', slug=course.slug)
    else:
        form = CourseUploadForm(instance=course)
    return render(request, 'courses/edit_course.html', {'form': form, 'course': course})

@login_required
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course__teacher=request.user)
    if request.method == 'POST':
        lesson.title = request.POST.get('title')
        lesson.lesson_type = request.POST.get('lesson_type')
        lesson.video_url = request.POST.get('video_url')
        lesson.is_preview = 'is_preview' in request.POST
        if request.FILES.get('content_file'):
            lesson.content_file = request.FILES.get('content_file')
        lesson.save()
        return redirect('course_detail_edit', slug=lesson.course.slug)
    return render(request, 'courses/edit_lesson.html', {'lesson': lesson})

@login_required
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course__teacher=request.user)
    course_slug = lesson.course.slug
    if request.method == 'POST':
        lesson.delete()
        return redirect('course_detail_edit', slug=course_slug)
    return render(request, 'courses/delete1_lesson_confirm.html', {'lesson': lesson})

@login_required
def student_dashboard(request):
    # Fetch courses where the current user is in the students ManyToMany field
    enrolled_courses = request.user.enrolled_courses.all()
    context = {
        'enrolled_courses': enrolled_courses, # Fixed typo in context key
        'full_name': request.user.get_full_name() or request.user.username
    }
    return render(request, 'courses/student_dashboard.html', context)

@login_required
def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.user not in course.students.all():
        course.students.add(request.user)
    return render(request, 'courses/enroll_success.html', {'course': course})