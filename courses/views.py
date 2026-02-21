from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth import login, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db.models import Q, Count, Prefetch

# Use get_user_model for compatibility with your custom user setup
User = get_user_model()

from .models import (
    MasterCategory, Course, Lesson, Carousel, SuccessStory, 
    StudyMaterial, YouTubeChannel, Module, Profile, ContactMessage
)
from .forms import (
    CourseUploadForm, RegistrationForm, ModuleFormSet, 
    UserUpdateForm, ProfileUpdateForm
)

# --- PUBLIC VIEWS ---

def home(request):
    context = {
        'categories': MasterCategory.objects.all().order_by('order'),
        'slides': Carousel.objects.filter(is_active=True),
        'popular_courses': Course.objects.filter(is_active=True)
                            .annotate(num_students=Count('students'))
                            .order_by('-num_students')[:4],
        'new_courses': Course.objects.filter(is_active=True).order_by('-created_at')[:4],
        'success_stories': SuccessStory.objects.all()[:3],
        'study_materials': StudyMaterial.objects.all().order_by('order'),
        'youtube_channels': YouTubeChannel.objects.all(),
    }
    return render(request, 'courses/home.html', context)

def all_courses(request):
    categories = MasterCategory.objects.prefetch_related(
        Prefetch('courses', queryset=Course.objects.filter(is_active=True))
    ).order_by('order')
    return render(request, 'courses/all_courses.html', {'categories': categories})

def category_detail(request, slug):
    category = get_object_or_404(MasterCategory, slug=slug)
    courses = Course.objects.filter(master_category=category, is_active=True)
    return render(request, 'courses/category_detail.html', {'category': category, 'courses': courses})

def about_us(request):
    context = {
        'total_students': User.objects.filter(profile__user_type='Student').count(),
        'total_teachers': User.objects.filter(profile__user_type='Teacher').count(),
        'total_courses': Course.objects.filter(is_active=True).count(),
    }
    return render(request, 'courses/about_us.html', context)

def contact_us(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            subject=request.POST.get('subject'),
            message=request.POST.get('message')
        )
        messages.success(request, "Your message has been sent successfully!")
        return redirect('contact_us')
    return render(request, 'courses/contact_us.html')

def search(request):
    query = request.GET.get('q')
    results = Course.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        is_active=True
    ) if query else []
    return render(request, 'courses/search_results.html', {'results': results, 'query': query})

# --- AUTH & PROFILE VIEWS ---

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Explicitly set user_type to override signal defaults
            profile = user.profile
            profile.user_type = form.cleaned_data.get('user_type', 'Student')
            profile.save()

            login(request, user)
            return redirect('login_success')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def live_classes(request):
    return render(request, 'courses/live_classes.html', {
        'live_courses': Course.objects.filter(is_live=True)
    })


@login_required
def login_success(request):
    if not hasattr(request.user, 'profile'):
        return redirect('/admin/' if request.user.is_staff else 'home')
    
    u_type = request.user.profile.user_type
    if u_type == 'Teacher':
        return redirect('teacher_dashboard')
    elif u_type == 'Admin':
        return redirect('/admin_dashboard/')
    return redirect('student_dashboard')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        # Fixed typo: request.POST.get('next') and request.build_absolute_uri()
        next_url = request.POST.get('next') 
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profile updated successfully!')
            
            if next_url and next_url != request.build_absolute_uri():
                return redirect(next_url)
            return redirect('home')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'courses/edit_profile.html', {'u_form': u_form, 'p_form': p_form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password updated successfully!')
            return redirect('home')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'courses/change_password.html', {'form': form})

# --- COURSE & LESSON VIEWS ---

def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    modules = course.modules.all().prefetch_related('lessons')
    return render(request, 'courses/course_detail.html', {'course': course, 'modules': modules})

def lesson_detail(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Check enrollment/preview status
    is_enrolled = request.user.is_authenticated and request.user in course.students.all()
    if not (lesson.is_preview or is_enrolled or request.user == course.teacher):
        return render(request, 'courses/lesson_locked.html', {'course': course, 'lesson': lesson})

    modules = course.modules.all().prefetch_related('lessons')
    return render(request, 'courses/lesson_player.html', {
        'course': course, 'lesson': lesson, 'modules': modules
    })

@login_required
def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.user not in course.students.all():
        course.students.add(request.user)
    return render(request, 'courses/enroll_success.html', {'course': course})

# --- DASHBOARDS ---

@login_required
def student_dashboard(request):
    enrolled_courses = request.user.enrolled_courses.all()
    return render(request, 'courses/student_dashboard.html', {
        'enrolled_courses': enrolled_courses,
        'full_name': request.user.get_full_name() or request.user.username
    })

@login_required
def teacher_dashboard(request):
    if request.user.profile.user_type != 'Teacher':
        return HttpResponseForbidden("Teachers Only")
    
    my_courses = Course.objects.filter(teacher=request.user).annotate(num_students=Count('students'))
    # Corrected logic for actual student count (Sum of students across all courses)
    actual_student_count = sum(c.num_students for c in my_courses)

    return render(request, 'courses/teacher_dashboard.html', {
        'my_course': my_courses,
        'total_courses': my_courses.count(),
        'total_students': actual_student_count,
    })

# --- TEACHER MANAGEMENT VIEWS ---

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
        form = CourseUploadForm()
    return render(request, 'courses/upload_course.html', {'form': form})

@login_required
def manage_curriculum(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)

    is_admin = request.user.profile.user_type == 'Admin' or request.user.is_superuser
    if course.teacher != request.user and not is_admin:
        return HttpResponseForbidden("Access Denied")

    if request.method == 'POST':
        formset = ModuleFormSet(request.POST, instance=course)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.master_category = course.master_category
                instance.save()
            formset.save_m2m()
            messages.success(request, 'Curriculum updated successfully!')

            if is_admin and 'admin-console' in request.META.get('HTTP_REFERER', ''):
                return redirect('/admin_dashboard/')
            return redirect('teacher_dashboard')
        
    else:
        formset = ModuleFormSet(instance=course)
    return render(request, 'courses/manage_curriculum.html', {'course': course, 'formset': formset})

@login_required
def course_detail_edit(request, slug):
    course = get_object_or_404(Course, slug=slug)
    is_admin = request.user.profile.user_type == 'Admin' or request.user.is_superuser

    if course.teacher != request.user and not is_admin:
        return HttpResponseForbidden("You do not have permission to edit this course.")
    
    modules = course.modules.all().prefetch_related('lessons')
    return render(request, 'courses/course_detail_edit.html',{
        'course': course, 
        'modules': modules, 
        'is_edit_mode': True
    })

@login_required
def edit_course(request, slug):
    course = get_object_or_404(Course, slug=slug)

    is_admin = request.user.profile.user_type == 'Admin' or request.user.is_superuser
    if course.teacher != request.user and not is_admin:
        return HttpResponseForbidden("Access Denied")

    if request.method == 'POST':
        form = CourseUploadForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_detail_edit', slug=course.slug)
    else:
        form = CourseUploadForm(instance=course)
    return render(request, 'courses/edit_course.html', {'form': form, 'course': course})

@login_required
def add_lesson(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course

    is_admin = request.user.profile.user_type == 'Admin' or request.user.is_superuser
    if course.teacher != request.user and not is_admin:
        return HttpResponseForbidden("Access Denied: You do not have permission to add lessons to this course.")
    
    if request.method == 'POST':
        Lesson.objects.create(
            module=module,
            course=module.course,
            title=request.POST.get('title'),
            lesson_type=request.POST.get('lesson_type'),
            video_url=request.POST.get('video_url'),
            content_file=request.FILES.get('content_file'),
            is_preview=request.POST.get('is_preview') == 'on',
            lecturer_name=request.user.get_full_name() or request.user.username
        )
        return redirect('manage_curriculum', course_slug=module.course.slug)
    return render(request, 'courses/add_lesson.html', {'module': module})

@login_required
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course

    is_admin = request.user.profile.user_type == 'Admin' or request.user.is_superuser
    if course.teacher != request.user and not is_admin:
        return HttpResponseForbidden("Access Denied: You do not have permission to edit this lesson.")

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
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    course_slug = lesson.course.slug

    is_admin = request.user.profile.user_type == 'Admin' or request.user.is_superuser
    if course.teacher != request.user and not is_admin:
        return HttpResponseForbidden("Access Denied")

    if request.method == 'POST':
        lesson.delete()
        return redirect('course_detail_edit', slug=course_slug)
    return render(request, 'courses/delete1_lesson_confirm.html', {'lesson': lesson})

@login_required
def admin_dashboard(request):

    if not (request.user.profile.user_type == 'Admin' or request.user.is_superuser):
        return HttpResponseForbidden("Access Denied Administrator Privileges Required")
    
    all_courses = Course.objects.all().annotate(num_students=Count('students'))
    total_courses = all_courses.count()
    all_teachers = User.objects.filter(profile__user_type='Teacher')

    context = {
        'all_courses': all_courses,
        'all_teachers': all_teachers,
        'platform_students': User.objects.filter(profile__user_type='Student').count(),
    }
    return render(request, 'courses/admin_dashboard.html', context)

@login_required
def assign_teacher(request, course_id):
    if not (request.user.profile.user_type == 'Admin' or request.user.is_superuser):
        return HttpResponseForbidden("Unauthorized")
    
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        teacher_id = request.POST.get('teacher_id')
        new_teacher = get_object_or_404(User, id=teacher_id)
        course.teacher = new_teacher
        course.save()
        messages.success(request, f"Course '{course.title}' assigned to {new_teacher.get_full_name()}'")
        return redirect('admin_dashboard')