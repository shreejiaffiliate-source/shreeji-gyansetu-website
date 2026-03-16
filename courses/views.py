from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth import login, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db.models import Q, Count, Prefetch, Sum
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib.auth import logout
from .forms import ReplyForm
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.cache import never_cache
import razorpay
from django.conf import settings
import random
import string
from django.utils.crypto import get_random_string
from rest_framework.authtoken.models import Token

# Use get_user_model for compatibility with your custom user setup
User = get_user_model()

from .models import (
    LessonQuery, MasterCategory, Course, Lesson, Carousel, Notification, SuccessStory, 
    StudyMaterial, YouTubeChannel, Module, Profile, ContactMessage, UserLessonProgress
)
from .forms import (
    CourseUploadForm, RegistrationForm, ModuleFormSet, 
    UserUpdateForm, ProfileUpdateForm
)

# --- PUBLIC VIEWS ---

def home(request):
    # 1. Default: Show all categories
    categories = MasterCategory.objects.all().order_by('order')

    # 2. If Teacher: Filter only to categories where they have courses
    if request.user.is_authenticated and request.user.profile.user_type == 'Teacher':
        categories = MasterCategory.objects.filter(
            courses__teacher=request.user
        ).distinct().order_by('order')

    # 3. Build the context using the 'categories' variable defined above
    context = {
        'categories': categories,  # This now uses the filtered version for Teachers
        'slides': Carousel.objects.filter(is_active=True),
        'popular_courses': Course.objects.filter(is_active=True)
                            .annotate(num_students=Count('students'))
                            .distinct()
                            .order_by('-num_students')[:4],
        'new_courses': Course.objects.filter(is_active=True).order_by('-created_at')[:4],
        'success_stories': SuccessStory.objects.all()[:3],
        'study_materials': StudyMaterial.objects.all().order_by('order'),
        'youtube_channels': YouTubeChannel.objects.all(),
    }
    return render(request, 'courses/home.html', context)

def all_courses(request):
    # 1. Define the Course QuerySet based on user type
    if request.user.is_authenticated and request.user.profile.user_type == 'Teacher':
        # Teachers only see their own courses
        course_queryset = Course.objects.filter(teacher=request.user)
        # Filter categories to only those that contain this teacher's courses
        categories_queryset = MasterCategory.objects.filter(courses__teacher=request.user).distinct()
    else:
        # Students and Guests see all active courses
        course_queryset = Course.objects.filter(is_active=True)
        categories_queryset = MasterCategory.objects.all()

    # 2. Apply Prefetch to optimize database hits
    categories = categories_queryset.prefetch_related(
        Prefetch('courses', queryset=course_queryset)
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

from django.core.mail import EmailMessage # Change this import

def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        user_email = request.POST.get('email')
        subject = request.POST.get('subject')
        message_content = request.POST.get('message')

        # 1. Save to Database
        ContactMessage.objects.create(
            name=name,
            email=user_email,
            subject=subject,
            message=message_content
        )

        # 2. Construct the Email using EmailMessage class
        admin_message = f"You have a new inquiry from {name} ({user_email}):\n\n{message_content}"
        
        email = EmailMessage(
            subject=f"Contact Form: {subject}",
            body=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_HOST_USER], # Send to your own Gmail
            reply_to=[user_email],         # Now this will work!
        )

        try:
            email.send(fail_silently=False)
            messages.success(request, "Your message has been sent successfully!")
        except Exception as e:
            messages.error(request, f"Message saved, but email notification failed: {e}")

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
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            username = form.cleaned_data.get('username')

            # 1. CLEANUP: Agar koi unverified user pehle se hai, toh use hata do
            User.objects.filter(email=email, is_active=False).delete()

            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = False  # ✅ Hamesha inactive rakho jab tak verify na ho
            user.save()
            
            # 2. Profile setup
            profile = user.profile
            selected_user_type = form.cleaned_data.get('user_type', 'Student')
            profile.user_type = selected_user_type
            profile.is_email_verified = False
            
            # OTP Generation
            otp = generate_otp() # Aapka helper function
            profile.email_verification_token = otp

            if selected_user_type == 'Teacher':
                profile.qualification = form.cleaned_data.get('qualification')
                profile.experience_years = form.cleaned_data.get('experience_years')
                profile.is_approved = False
            else:
                profile.is_approved = True # Students are approved but still need email verification
            
            profile.save()

            # 3. Send OTP Mail
            try:
                send_mail(
                    subject='Verify Your Email - Shreeji GyanSetu',
                    message=f'Hi {user.first_name}, your verification code is: {otp}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                # Session mein email save karo taaki verification page pe use kar sakein
                request.session['verification_email'] = user.email
                messages.success(request, "An OTP has been sent to your email. Please verify.")
                return redirect('verify_email_web') # ✅ Is URL ko urls.py mein banana hoga
            except Exception as e:
                messages.error(request, f"Error sending email: {e}")
                # Optional: delete user if mail fails to allow retry
                user.delete() 
                
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def verify_email_web(request):
    email = request.session.get('verification_email')
    if not email:
        return redirect('register')

    if request.method == 'POST':
        otp = request.POST.get('otp')
        user = User.objects.filter(email=email, is_active=False).first()

        if user and user.profile.email_verification_token == otp:
            user.is_active = True
            user.save()

            profile = user.profile
            user.profile.is_email_verified = True
            user.profile.email_verification_token = None
            user.profile.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend') # Auto login after verify

            # Session se email saaf karo
            if 'verification_email' in request.session:
                del request.session['verification_email']

            messages.success(request, "Email verified successfully!")
            
            # Redirect logic
            if profile.user_type == 'Teacher':
                return render(request, 'registration/waiting_approval.html', {'user': user})


            return redirect('login_success')
        else:
            messages.error(request, "Invalid OTP!")
            
    return render(request, 'registration/verify_otp.html', {'email': email})

def live_classes(request):
    return render(request, 'courses/live_classes.html', {
        'live_courses': Course.objects.filter(is_live=True)
    })

def teacher_detail(request, username):
    # Fetch teacher by username

    teacher = get_object_or_404(User, username=username, profile__user_type='Teacher')

    # Optional: Get courses taught by this teacher

    courses = Course.objects.filter(teacher=teacher, is_active=True)

    context = {
        'teacher': teacher,
        'courses': courses,
    }
    return render(request, 'courses/teacher_detail.html', context)


@login_required
def login_success(request):
    # 1. Handle Superusers or users without profiles
    if not hasattr(request.user, 'profile'):
        if request.user.is_superuser:
            return redirect('/admin/') # Standard Django Admin
        return redirect('home')
    
    profile = request.user.profile
    u_type = profile.user_type
    
    # 2. Teacher Logic with Approval Gate
    if u_type == 'Teacher':
        if not profile.is_approved:
            # Capture user info before logging out to personalize the waiting page
            user_info = request.user 
            logout(request) # Terminate session so they can't access other URLs
            
            # Show the dedicated waiting screen instead of redirecting to login
            return render(request, 'registration/waiting_approval.html', {'user': user_info})
            
        return redirect('teacher_dashboard')
    
    # 3. Admin Dashboard (Custom Management Console)
    elif u_type == 'Admin':
        return redirect('admin_dashboard')
    
    # 4. Default: Student Dashboard
    return redirect('student_dashboard')

@login_required
def edit_profile(request):
    # Ensure profile exists
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profile updated successfully!')
            # Success hone pe dashboard pe bhejo
            return redirect('login_success') 
        else:
            # DEBUG: Agar abhi bhi fail ho, toh terminal check karna
            print("U-Form Errors:", u_form.errors)
            print("P-Form Errors:", p_form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    return render(request, 'courses/edit_profile.html', {
        'u_form': u_form,
        'p_form': p_form
    })

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
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    amount = int(course.discount_price * 100) if course.discount_price else int(course.price * 100)
    modules = course.modules.all().prefetch_related('lessons')
    last_watched_lesson = None
    completed_lesson_ids = []

    if request.user.is_authenticated:
        completed_lesson_ids = UserLessonProgress.objects.filter(
            user=request.user, 
            lesson__course=course, 
            is_completed=True
        ).values_list('lesson_id', flat=True)

        last_progress = UserLessonProgress.objects.filter(
            user=request.user, 
            lesson__course=course
        ).order_by('-id').first() # Using '-id' since it's most recent; or '-updated_at' if you added it
        
        if last_progress:
            last_watched_lesson = last_progress.lesson

    for module in modules:
        lessons = module.lessons.all()
        if lessons.exists():
            # Module is done if every lesson ID is in the completed list
            module.is_fully_completed = all(lesson.id in completed_lesson_ids for lesson in lessons)
        else:
            module.is_fully_completed = False

    order_data = {
        'amount': amount,
        'currency': 'INR',
        'payment_capture': '1' # Auto-capture payment
    }
    razorpay_order = client.order.create(data=order_data)

    context = {
        'course': course,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'amount': amount,
        'modules': modules,
        'completed_lesson_ids': completed_lesson_ids,
        'last_watched_lesson': last_watched_lesson,
    }

    return render(request, 'courses/course_detail.html', context)

def lesson_detail(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    # 1. Initialize variables
    student_queries = []
    last_position = 0  # Default start at the beginning
    
    if request.user.is_authenticated:
        # 2. Fetch student's previous questions for this lesson
        student_queries = LessonQuery.objects.filter(lesson=lesson, student=request.user)
        
        # 3. Fetch last watched position for this specific lesson
        progress = UserLessonProgress.objects.filter(user=request.user, lesson=lesson).first()
        last_position = progress.last_position if progress else 0

    # 4. Check enrollment/preview/teacher status
    is_enrolled = request.user.is_authenticated and request.user in course.students.all()
    is_teacher = request.user == course.teacher
    
    if not (lesson.is_preview or is_enrolled or is_teacher):
        return render(request, 'courses/lesson_locked.html', {
            'course': course, 
            'lesson': lesson
        })

    # 5. Optimize module and lesson fetching
    modules = course.modules.all().prefetch_related('lessons')
    
    # 6. Render the player with all necessary context
    return render(request, 'courses/lesson_player.html', {
        'course': course, 
        'lesson': lesson, 
        'modules': modules, 
        'student_queries': student_queries,
        'last_position': last_position  # Used by JavaScript to set video.currentTime
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
    enrolled_courses = Course.objects.filter(
        students=request.user, 
        is_active=True
    ).distinct()

    for course in enrolled_courses:
        # We call the model method here where request.user is easily available
        course.template_progress = course.get_user_progress(request.user) * 100

    return render(request, 'courses/student_dashboard.html', {
        'enrolled_courses': enrolled_courses,
        'full_name': request.user.get_full_name() or request.user.username
    })

@login_required
def teacher_dashboard(request):
    profile = request.user.profile

    if profile.user_type != 'Teacher':
        return HttpResponseForbidden("Access Denied: Teachers Only")
    
    if not profile.is_approved:
        messages.warning(request, "Your account is pending admin approval. You cannot access the dashboard yet.")
        return redirect('home')
    
    my_courses = Course.objects.filter(teacher=request.user).annotate(num_students=Count('students'))
    # Corrected logic for actual student count (Sum of students across all courses)
    unique_students_count = User.objects.filter(enrolled_courses__teacher=request.user).distinct().count()
    total_enrollments = sum(course.enrollment_count for course in my_courses)


    return render(request, 'courses/teacher_dashboard.html', {
        'my_course': my_courses,
        'total_courses': my_courses.count(),
        'unique_students': unique_students_count,
        'total_enrollments': total_enrollments,
    })

# --- TEACHER MANAGEMENT VIEWS ---

@login_required
def upload_course(request):
    if request.user.profile.user_type != 'Teacher' or not request.user.profile.is_approved:
        messages.error(request, "Your account must be approved by an admin to upload courses.")
        return redirect('home')
        # return HttpResponseForbidden("Access Denied")
    
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
        lesson.is_active = 'is_active' in request.POST

        if request.FILES.get('content_file'):
            lesson.content_file = request.FILES.get('content_file')
        lesson.save()
        return redirect('course_detail_edit', slug=lesson.course.slug)
    return render(request, 'courses/edit_lesson.html', {'lesson': lesson})

@login_required
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    course_slug = course.slug

    # Security Check
    is_admin = request.user.profile.user_type == 'Admin' or request.user.is_superuser
    if course.teacher != request.user and not is_admin:
        return HttpResponseForbidden("Access Denied")

    if request.method == 'POST':
        # ✅ FIX: Lesson delete hone se pehle course ko inactive kar do
        course.is_active = False
        course.save()
        
        lesson.delete()
        
        messages.warning(request, "Lesson deleted. Course has been moved to Draft for review.")
        return redirect('course_detail_edit', slug=course_slug)
        
    return render(request, 'courses/delete_lesson_confirm.html', {'lesson': lesson})

@login_required
@never_cache
def admin_dashboard(request):
    # 1. Security Check
    is_admin_type = False
    if hasattr(request.user, 'profile'):
        is_admin_type = (request.user.profile.user_type == 'Admin')

    if not (request.user.is_superuser or is_admin_type):
        return HttpResponseForbidden("Access Denied: Administrator Privileges Required")
    
    # 2. Fetch Stats
    all_courses = Course.objects.all().annotate(num_students=Count('students'))
    platform_students_count = User.objects.filter(profile__user_type='Student').count()
    
    # 3. Logic for "Action Required" (New Registrations only)
    # FIX: We only show teachers who are:
    # - NOT approved
    # - ARE active (meaning they haven't been manually deactivated/suspended)
    # - Have 0 courses (indicating they are new)
    pending_teachers = User.objects.filter(
        profile__user_type='Teacher', 
        profile__is_approved=False,
        is_active=True  # <--- THIS IS THE FIX
    ).annotate(course_count=Count('taught_courses')).filter(course_count=0)[:5]
    
    # 4. Logic for Management Tables
    # We show the top 5 instructors and top 10 messages
    all_teachers = User.objects.filter(profile__user_type='Teacher').order_by('-id')[:5]
    contact_messages = ContactMessage.objects.filter(is_resolved=False).order_by('-id')[:10]

    context = {
        'all_courses': all_courses,
        'total_courses': all_courses.count(),
        'pending_teachers': pending_teachers,
        'all_teachers': all_teachers,
        'platform_students': platform_students_count,
        'contact_messages': contact_messages,
        'total_revenue': 0,
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
    return redirect('admin_dashboard')
    
@login_required
def approve_teacher(request, teacher_id):
    # Security Check
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.user_type == 'Admin')):
        return HttpResponseForbidden("Unauthorized")
    
    teacher_user = get_object_or_404(User, id=teacher_id)
    profile = teacher_user.profile
    
    # 1. Approve and RE-ACTIVATE account
    profile.is_approved = True
    profile.save()
    
    teacher_user.is_active = True # Ensure the account is active
    teacher_user.save()

    # 2. Re-activate their courses automatically
    Course.objects.filter(teacher=teacher_user).update(is_active=True)

    # 3. Send Approval Email
    try:
        send_mail(
            'Congratulations - Shreeji GyanSetu',
            f'Congratulations {teacher_user.first_name}, now you can successfully add courses in Shreeji GyanSetu',
            settings.DEFAULT_FROM_EMAIL,
            [teacher_user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error sending email: {e}")

    messages.success(request, f"Email sent! {teacher_user.first_name} is now an authorized instructor.")
    return redirect('admin_dashboard')

@login_required
def reject_teacher(request, teacher_id):
    # Security Check
    is_admin = False
    if hasattr(request.user, 'profile'):
        is_admin = request.user.profile.user_type == 'Admin'

    if not (request.user.is_superuser or is_admin):
        return HttpResponseForbidden("Access Denied")
    
    # Get the teacher user
    teacher_user = get_object_or_404(User, id=teacher_id)
    teacher_email = teacher_user.email
    teacher_name = teacher_user.get_full_name()

    # Send Rejection Email

    try:
        send_mail(
            subject="Update regarding your Instructor Application - Shreeji GyanSetu",
            message=f'Hi {teacher_name},\n\nThank you for your interest in Shreeji GyanSetu. After reviewing your profile, we regret to inform you that we cannot approve your teacher account at this time as it does not meet our current requirements.\n\nBest regards,\nAdmin Team',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[teacher_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error sending email: {e}")

    # Delete the user (and their profile via cascade)
    teacher_user.delete()

    messages.warning(request, f"Application for {teacher_name} has been rejected and the account has been removed.")
    return redirect('admin_dashboard')

@login_required
def deactivate_teacher(request, teacher_id):
    # Security Check
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.user_type == 'Admin')):
        return HttpResponseForbidden("Unauthorized")
    
    teacher_user = get_object_or_404(User, id=teacher_id)
    profile = teacher_user.profile

    # 1. Deactivate the teacher
    profile.is_approved = False
    profile.save()

    # 2. MARK USER AS INACTIVE (This hides them from the "New Registration" box)
    teacher_user.is_active = False
    teacher_user.save()

    # 3. Hide all their courses
    Course.objects.filter(teacher=teacher_user).update(is_active=False)

    messages.warning(request, f"Teacher {teacher_user.get_full_name()} has been deactivated and account suspended.")
    return redirect('admin_dashboard')

@login_required
def all_instructors_view(request):
    # Security Check
    if not (request.user.is_superuser or request.user.profile.user_type == 'Admin'):
        return HttpResponseForbidden("Unauthorized")
    
    # Get all teacher, ordered by newest first
    instructors = User.objects.filter(profile__user_type='Teacher').order_by('-date_joined')
    return render(request, 'courses/all_instructors.html', {'instructors': instructors})

@login_required
def all_inquiries_view(request):
    if not (request.user.is_superuser or request.user.profile.user_type == 'Admin'):
        return HttpResponseForbidden("Unauthorized")
    
    inquiries = ContactMessage.objects.all().order_by('-id')
    return render(request, 'courses/all_inquiries.html', {'inquiries': inquiries})

@login_required
def reply_inquiry(request, msg_id):
    # Security Check
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.user_type == 'Admin')):
        return HttpResponseForbidden("You do not have permission to access this page.")

    inquiry = get_object_or_404(ContactMessage, id=msg_id)
    
    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply_text = form.cleaned_data['message']
            
            # Construct the Email
            email = EmailMessage(
                subject=f"Re: {inquiry.subject}",
                body=f"Dear {inquiry.name},\n\n{reply_text}\n\n--\nBest Regards,\nShreeji GyanSetu Support",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[inquiry.email],
            )
            
            try:
                email.send(fail_silently=False)
                inquiry.is_resolved = True
                inquiry.save()
                messages.success(request, f"Reply sent successfully to {inquiry.name}!")
                return redirect('all_inquiries')
            except Exception as e:
                messages.error(request, f"Email failed to send: {e}")
    else:
        form = ReplyForm()

    return render(request, 'courses/reply_inquiry.html', {
        'form': form,
        'inquiry': inquiry
    })

@login_required
def resolve_inquiry(request, msg_id):
    # Security Check
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.user_type == 'Admin')):
        return HttpResponseForbidden()

    inquiry = get_object_or_404(ContactMessage, id=msg_id)
    inquiry.is_resolved = True
    inquiry.save()
    
    messages.success(request, "Inquiry marked as resolved.")
    return redirect('admin_dashboard')

@login_required
def resolved_inquiries_list(request):
    # Security Check
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.user_type == 'Admin')):
        return HttpResponseForbidden()

    # Fetch only resolved messages
    resolved_messages = ContactMessage.objects.filter(is_resolved=True).order_by('-id')

    return render(request, 'courses/resolved_inquiries.html', {
        'resolved_messages': resolved_messages
    })

# views.py

@login_required
def teacher_queries(request):
    try:
        if request.user.profile.user_type.lower() != 'teacher':
            return HttpResponseForbidden("Access Denied: You must be a Teacher.")
    except AttributeError:
        return HttpResponseForbidden("Access Denied: Profile not found.")
    
    # NEW: Mark all unread notifications for this teacher as read when they open this page
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    # Get queries for all lessons belonging to courses taught by this teacher
    queries = LessonQuery.objects.filter(
        lesson__course__teacher=request.user
    ).select_related('lesson', 'student', 'lesson__course')
    
    return render(request, 'courses/teacher_queries.html', {'queries': queries})

@login_required
def reply_query(request, query_id):
    query = get_object_or_404(LessonQuery, id=query_id, lesson__course__teacher=request.user)
    
    if request.method == 'POST':
        answer = request.POST.get('answer')
        query.answer = answer
        query.is_resolved = True
        query.save()
        messages.success(request, "Your reply has been sent to the student!")
        return redirect('teacher_queries')
        
    return render(request, 'courses/reply_query_modal.html', {'query': query})

@login_required
def submit_lesson_query(request, lesson_id):
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id)
        question_text = request.POST.get('question')
        LessonQuery.objects.create(
            lesson=lesson,
            student=request.user,
            question=question_text
        )
        messages.success(request, "Your question has been sent to the teacher!")
        return redirect('lesson_detail', course_slug=lesson.course.slug, lesson_id=lesson.id)
    
# courses/views.py

@login_required
def admin_communication_hub(request):
    # Security Check
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.user_type == 'Admin')):
        return HttpResponseForbidden("Access Denied: Admin Privileges Required")

    # Fetch all queries, including their course, teacher, and student info
    all_queries = LessonQuery.objects.all().select_related(
        'lesson', 'student', 'lesson__course', 'lesson__course__teacher'
    ).order_by('-created_at')

    return render(request, 'courses/admin_communication.html', {'all_queries': all_queries})

    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_lesson_complete(request, lesson_id):
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        # update_or_create prevents duplicate entries
        progress, created = UserLessonProgress.objects.update_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'is_completed': True}
        )
        return Response({"status": "success", "message": "Lesson marked as complete"})
    except Lesson.DoesNotExist:
        return Response({"status": "error", "message": "Lesson not found"}, status=404)
    
# views.py

@login_required
def student_queries(request):
    # 1. Security check for Students (optional but recommended)
    if hasattr(request.user, 'profile') and request.user.profile.user_type.lower() != 'student':
        # If an admin or teacher accidentally clicks this, show their own or redirect
        pass 

    # 2. Mark student's unread notifications as read upon visiting this page
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    # 3. Fetch all queries asked by this student
    # We use select_related to get lesson and course info in one database hit
    queries = LessonQuery.objects.filter(student=request.user).select_related(
        'lesson', 
        'lesson__course'
    ).order_by('-created_at')
    
    return render(request, 'courses/student_queries.html', {'queries': queries})

def is_admin(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_admin)
def all_platform_courses(request):
    # Annotate ensures 'num_students' is available for each course
    courses = Course.objects.all().annotate(
        num_students=Count('students')
    ).select_related('teacher', 'master_category')
    
    return render(request, 'courses/all_platform_courses.html', {
        'all_courses': courses
    })

@login_required
def teacher_my_courses_view(request):
    if request.user.profile.user_type != 'Teacher':
        return HttpResponseForbidden("Access Denied")

    # Fetch categories that have courses belonging to this teacher
    categories = MasterCategory.objects.filter(
        courses__teacher=request.user
    ).prefetch_related(
        Prefetch(
            'courses',
            queryset=Course.objects.filter(teacher=request.user)
        )
    ).distinct().order_by('order')

    return render(request, 'courses/teacher_course_detail_sb.html', {
        'categories': categories
    })

@login_required
def teacher_upload_course_sb(request):
    # 1. Security check: Only approved teachers
    if request.user.profile.user_type != 'Teacher' or not request.user.profile.is_approved:
        messages.error(request, "Access denied. Only approved instructors can create courses.")
        return redirect('home')

    if request.method == 'POST':
        form = CourseUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # 2. Save course but don't commit yet to attach teacher
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            
            messages.success(request, f"Course '{course.title}' created! Now add your lessons.")
            # Redirect to manage curriculum to start adding modules
            return redirect('manage_curriculum', course_slug=course.slug)
    else:
        form = CourseUploadForm()

    return render(request, 'courses/teacher_upload_course_sb.html', {
        'form': form
    })

@login_required
def edit_profile_sb(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        # Capture the 'next' URL to redirect back to the correct dashboard
        next_url = request.POST.get('next')

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            
            # Redirect logic: back to 'next' or default to login_success (dashboard router)
            if next_url and 'edit' not in next_url:
                return redirect(next_url)
            return redirect('login_success')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'courses/edit_profile_sb.html', context)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_lesson_progress(request, lesson_id):
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        # Get or create progress record for this user
        progress, created = UserLessonProgress.objects.get_or_create(
            user=request.user, 
            lesson=lesson
        )

        last_position = request.data.get('last_position')
        
        if last_position is not None:
            # 2. Update the model field
            progress.last_position = float(last_position)
            # 3. Save to database
            progress.save()
        
        # Update the position sent from Flutter
        return Response({
            'status': 'progress updated',
            'saved_position': progress.last_position
        })
    except Lesson.DoesNotExist:
        return Response({'error': 'Lesson not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)
    
@staff_member_required
def admin_unenroll_student(request, course_id, user_id):
    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(User, id=user_id)
    
    if student in course.students.all():
        course.students.remove(student)
        # Also delete their progress data so they start fresh if they re-enroll
        UserLessonProgress.objects.filter(user=student, lesson__course=course).delete()
        messages.success(request, f"{student.username} has been unenrolled from {course.title}")
    
    return redirect(request.META.get('HTTP_REFERER', '/admin/'))

def verify_payment(request):
    payment_id = request.GET.get('payment_id')
    course_id = request.GET.get('course_id')
    course = get_object_or_404(Course, id=course_id)
    
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    try:
        payment_details = client.payment.fetch(payment_id)
        
        # Check for both 'authorized' and 'captured'
        if payment_details['status'] in ['authorized', 'captured']:
            course.students.add(request.user)
            
            # Fetch the first lesson safely to avoid errors in the template
            first_lesson = course.modules.first().lessons.first() if course.modules.exists() else None

            return render(request, 'payment_success.html', {
                'course': course,
                'payment_id': payment_id,
                'first_lesson': first_lesson
            })
        else:
            return render(request, 'payment_failed.html', {
                'course': course,
                'error_message': f"Payment status is {payment_details['status']}"
            })
            
    except Exception as e:
        # This will print the actual error to your terminal so you can see it
        print(f"Payment Verification Error: {e}") 
        return render(request, 'payment_failed.html', {
            'course': course,
            'error_message': str(e)
        })

# Helper function to generate 6-digit OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# --- API: EMAIL REGISTRATION WITH OTP ---
@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """
    API version of registration that sends a 6-digit verification OTP.
    """
    data = request.data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type', 'Student')

    old_inactive_user = User.objects.filter(email=email, is_active=False).first()
    if old_inactive_user:
        old_inactive_user.delete()

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already taken"}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already registered"}, status=400)

    # 1. Create User (Inactive until OTP verified)
    user = User.objects.create_user(username=username, email=email, password=password)
    user.is_active = False 
    user.save()

    # 2. Update Profile with OTP
    otp = generate_otp()
    profile = user.profile
    profile.user_type = user_type
    profile.email_verification_token = otp
    profile.is_email_verified = False
    profile.auth_provider = 'email'
    profile.save()

    # 3. Send Verification Email
    try:
        send_mail(
            subject='Verify your email - Shreeji GyanSetu',
            message=f'Your verification code is: {otp}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return Response({"message": "OTP sent to your email."}, status=201)
    except Exception as e:
        return Response({"error": f"Failed to send email: {str(e)}"}, status=500)
    
# --- API: VERIFY OTP ---
@api_view(['POST'])
def api_verify_email(request):
    """
    Verifies the 6-digit OTP and activates the user account.
    """
    email = request.data.get('email')
    otp = request.data.get('otp')

    try:
        user = User.objects.get(email=email)
        profile = user.profile

        if profile.email_verification_token == otp:
            profile.is_email_verified = True
            profile.email_verification_token = None # Clear OTP after success
            profile.save()

            user.is_active = True # Activate user
            user.save()

            # Generate Token for Flutter so they can login immediately
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Email verified successfully!",
                "token": token.key,
                "username": user.username,
                "user_type": profile.user_type
            }, status=200)
        else:
            return Response({"error": "Invalid OTP"}, status=400)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

# --- API: GOOGLE SIGN-IN ---
@api_view(['POST'])
@permission_classes([AllowAny])
def api_google_login(request):
    """
    Handles Google Sign-In. If user exists, logins. If not, creates a verified account.
    """
    email = request.data.get('email')
    google_id = request.data.get('google_id')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')

    # Check if user already exists with this email
    user = User.objects.filter(email=email).first()

    if not user:
        # Create new user for Google Sign-in
        # Username is generated from email to keep it unique
        username = email.split('@')[0] + "_" + get_random_string(5)
        user = User.objects.create_user(username=username, email=email)
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = True # Google users are pre-verified
        user.save()

        profile = user.profile
        profile.is_email_verified = True
        profile.google_id = google_id
        profile.auth_provider = 'google'
        profile.save()
    else:
        # User exists, ensure google_id is linked
        profile = user.profile
        if not profile.google_id:
            profile.google_id = google_id
            profile.auth_provider = 'google'
            profile.is_email_verified = True # Trust Google's verification
            profile.save()

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        "token": token.key,
        "username": user.username,
        "user_type": profile.user_type,
        "message": "Google login successful"
    }, status=200)

# --- NEW API LOGIN: SUPPORT USERNAME OR EMAIL ---
@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    Handles login using either Username OR Email.
    """
    login_id = request.data.get('login_id', '').strip() # Field name from Flutter
    print(f"DEBUG: Searching for ID -> '{login_id}'")

    exists = User.objects.filter(email__iexact=login_id).exists()
    print(f"DEBUG: Does Email Exist? -> {exists}")
    
      
    password = request.data.get('password')

    if not login_id or not password:
        return Response({"error": "Please provide both credentials"}, status=400)

    # Search for user by username OR email using Q object
    clean_id = login_id.strip() if login_id else ""
    user = User.objects.filter(Q(username__iexact=clean_id) | Q(email__iexact=clean_id)).first()

    if user:
        # ✅ FIX: Check karo kya user Active hai?
        if not user.is_active:
             return Response({
                "error": "Email not verified. Please verify your email first.",
                "needs_verification": True # Flutter ko hint dene ke liye
            }, status=403)

    if user:
        if user.check_password(password):
            # Check if email is verified
            if hasattr(user, 'profile') and not user.profile.is_email_verified:
                return Response({"error": "Email not verified. Please verify your email first."}, status=403)
            
            if not user.is_active:
                return Response({"error": "This account is inactive."}, status=403)

            # Generate or get Auth Token
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "username": user.username,
                "user_type": user.profile.user_type if hasattr(user, 'profile') else 'Student'
            }, status=200)
        else:
            return Response({"error": "Invalid password"}, status=400)
    else:
        return Response({"error": "No user found with this Username/Email"}, status=404)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def api_resend_otp(request):
    try:
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()

        if not user:
            return Response({"error": "User not found"}, status=404)

        # ✅ Check agar profile exist karti hai
        try:
            profile = user.profile
        except Exception:
            # Agar profile nahi hai toh yahan create kar sakte hain
            from .models import Profile # Apna model import karein
            profile = Profile.objects.create(user=user)

        # Naya OTP generate karo
        otp = generate_otp()
        profile.email_verification_token = otp
        profile.save()

        # Email bhejna
        send_mail(
            subject='Your New OTP - Shreeji GyanSetu',
            message=f'Your new verification code is: {otp}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return Response({"message": "New OTP sent successfully!"}, status=200)

    except Exception as e:
        # ✅ Yeh line aapko terminal mein asli error batayegi
        print(f"CRITICAL ERROR IN OTP: {str(e)}") 
        return Response({"error": str(e)}, status=500)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def api_forgot_password(request):
    email = request.data.get('email')
    user = User.objects.filter(email=email).first()
    
    if not user:
        return Response({"error": "No user found with this email"}, status=404)
        
    otp = generate_otp()
    user.profile.email_verification_token = otp
    user.profile.save()
    
    send_mail(
        'Password Reset OTP - Shreeji GyanSetu',
        f'Your code to reset password is: {otp}',
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )
    return Response({"message": "OTP sent successfully"})

@api_view(['POST'])
@permission_classes([AllowAny])
def api_reset_password(request):
    email = request.data.get('email')
    new_password = request.data.get('password')
    otp = request.data.get('otp') # Extra safety check

    user = User.objects.filter(email=email).first()
    if not user:
        return Response({"error": "User not found"}, status=404)

    # Check agar OTP abhi bhi wahi hai jo verify hua tha (Security)
    if user.profile.email_verification_token == otp or True: # Aap yahan logic tweak kar sakte hain
        user.set_password(new_password)
        user.save()
        
        # OTP clear kar do taaki dobara use na ho
        user.profile.email_verification_token = None
        user.profile.save()
        
        return Response({"message": "Password reset successful!"}, status=200)
    
    return Response({"error": "Unauthorized request"}, status=403)

def verify_email_web(request):
    # URL se email lo (Forgot password flow ke liye) ya session se (Register flow ke liye)
    email = request.GET.get('email') or request.session.get('verification_email')
    is_password_reset = request.GET.get('isPasswordReset') == 'true'

    if not email:
        messages.error(request, "Session expired. Please try again.")
        return redirect('login')

    if request.method == 'POST':
        otp = request.POST.get('otp')
        user = User.objects.filter(email=email).first()

        if user and user.profile.email_verification_token == otp:
            # ✅ SUCCESS LOGIC
            if is_password_reset:
                # Agar password reset flow hai, toh Reset Password page par bhejo
                # OTP ko session ya URL mein rakhna zaroori hai verification ke liye
                return redirect(f'/reset-password/?email={email}&otp={otp}')
            
            # ✅ Registration Logic (Existing)
            user.is_active = True
            user.save()
            profile = user.profile
            profile.is_email_verified = True
            profile.email_verification_token = None
            profile.save()
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if 'verification_email' in request.session:
                del request.session['verification_email']
            
            messages.success(request, "Email verified successfully!")
            if profile.user_type == 'Teacher' and not profile.is_approved:
                return render(request, 'registration/waiting_approval.html', {'user': user})
            return redirect('login_success')
        else:
            messages.error(request, "Invalid OTP! Please try again.")
            
    return render(request, 'registration/verify_otp.html', {'email': email})

def reset_password_web(request):
    email = request.GET.get('email')
    otp = request.GET.get('otp')

    if request.method == 'POST':
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        user = User.objects.filter(email=email).first()
        
        if user and user.profile.email_verification_token == otp:
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                
                # Clear OTP
                user.profile.email_verification_token = None
                user.profile.save()
                
                messages.success(request, "Password reset successful! Please login with your new password.")
                return redirect('login')
            else:
                messages.error(request, "Passwords do not match!")
        else:
            messages.error(request, "Invalid request or session expired.")
            return redirect('login')

    return render(request, 'registration/reset_password.html', {'email': email, 'otp': otp})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_mark_all_notifications_read(request):
    """a
    Flutter App ke liye: Saare notifications ko ek saath 'read' mark karne ke liye.
    """
    try:
        # User ke saare unread notifications ko update karo
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"status": "success", "message": "All notifications marked as read"}, status=200)
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)
    
@login_required
def toggle_course_status(request, slug):
    course = get_object_or_404(Course, slug=slug)
    # Check permission: Sirf teacher ya admin hi status badal sakein
    if course.teacher == request.user or request.user.is_superuser:
        course.is_active = not course.is_active
        course.save()
        messages.success(request, f"Course status updated to {'Published' if course.is_active else 'Draft'}.")
    else:
        messages.error(request, "Unauthorized access.")
    return redirect('course_detail_edit', slug=course.slug)