from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Import views from courses app
from courses.views import (
    home, category_detail, course_detail, lesson_detail, search, 
    teacher_dashboard, upload_course, manage_curriculum, login_success, 
    add_lesson, register, course_detail_edit, edit_course, edit_lesson, 
    delete_lesson, student_dashboard, enroll_course, all_courses, 
    about_us, contact_us, edit_profile, change_password, admin_dashboard, 
    assign_teacher, live_classes, teacher_detail, reject_teacher, 
    approve_teacher, deactivate_teacher, all_inquiries_view, 
    all_instructors_view, reply_inquiry, resolve_inquiry, 
    resolved_inquiries_list, mark_lesson_complete, teacher_queries, 
    reply_query, submit_lesson_query, admin_communication_hub, 
    student_queries, all_platform_courses, teacher_my_courses_view,
    teacher_upload_course_sb, edit_profile_sb
)
from courses import api_views
from rest_framework.authtoken.views import obtain_auth_token

admin.site.site_header = "Shreeji GyanSetu Administration"
admin.site.site_title = "GyanSetu Admin Portal"
admin.site.index_title = "Welcome to Shreeji GyanSetu Management"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name='home'),
    path('chained_filter/', include('smart_selects.urls')),
    path('category/<slug:slug>/', category_detail, name='category_detail'),
    path('course/<slug:slug>/', course_detail, name='course_detail'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/', lesson_detail, name='lesson_detail'),
    path('search/', search, name='search'),
    
    # Dashboards
    path('dashboard/teacher/', teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/student/', student_dashboard, name='student_dashboard'), # Standardized path
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    
    # Auth
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('login-success/', login_success, name='login_success'),
    path('register/', register, name='register'),
    
    # Teacher Management
    path('dashboard/teacher/upload/', upload_course, name='upload_course'),
    path('course/<slug:course_slug>/manage-curriculum/', manage_curriculum, name='manage_curriculum'),
    path('module/<int:module_id>/add-lesson/', add_lesson, name='add_lesson'),
    path('course/<slug:slug>/manage/', course_detail_edit, name='course_detail_edit'),
    path('course/<slug:slug>/edit/', edit_course, name='edit_course'),
    path('lesson/<int:lesson_id>/edit/', edit_lesson, name='edit_lesson'),
    path('lesson/<int:lesson_id>/delete/', delete_lesson, name='delete_lesson'),
    path('dashboard/teacher/queries/', teacher_queries, name='teacher_queries'),
    path('dashboard/teacher/queries/<int:query_id>/reply/', reply_query, name='reply_query'),
    path('dashboard/teacher/my-courses/', teacher_my_courses_view, name='teacher_my_courses'),
    path('dashboard/teacher/create-course/', teacher_upload_course_sb, name='teacher_upload_course_sb'),
    
    # Student Actions
    path('course/<slug:slug>/enroll/', enroll_course, name='enroll_course'),
    path('lesson/<int:lesson_id>/query/', submit_lesson_query, name='submit_lesson_query'),
    path('my-queries/', student_queries, name='student_queries'),
    
    # Public & General
    path('courses/', all_courses, name='all_courses'),
    path('about/', about_us, name='about_us'),
    path('contact/', contact_us, name='contact_us'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('password/change/', change_password, name='change_password'),
    path('live-classes/', live_classes, name='live_classes'),
    path('teacher/<str:username>/', teacher_detail, name='teacher_detail'),
    path('dashboard/profile/edit/', edit_profile_sb, name='edit_profile_sb'),
    
    # Admin Console
    path('admin-console/courses/', all_platform_courses, name='all_platform_courses'),
    path('admin-console/instructors/', all_instructors_view, name='all_instructors'),
    path('admin-console/inquiries/', all_inquiries_view, name='all_inquiries'),
    path('admin-console/communication/', admin_communication_hub, name='admin_communication'),
    path('admin-console/inquiry/reply/<int:msg_id>/', reply_inquiry, name='reply_inquiry'),
    path('admin-console/resolved-inquiries/', resolved_inquiries_list, name='resolved_inquiries_list'),
    
    # Admin Actions
    path('assign-teacher/<int:course_id>/', assign_teacher, name='assign_teacher'),
    path('reject-teacher/<int:teacher_id>/', reject_teacher, name='reject_teacher'),
    path('approve-teacher/<int:teacher_id>/', approve_teacher, name='approve_teacher'),
    path('deactivate-teacher/<int:teacher_id>/', deactivate_teacher, name='deactivate_teacher'),
    path('resolve-inquiry/<int:msg_id>/', resolve_inquiry, name='resolve_inquiry'),

    # API Endpoints
    path('api/', api_views.ApiRoot.as_view(), name='api_root'),
    path('api/login/', obtain_auth_token, name='api_token_auth'), # Returns a Token
    path('api/register/', api_views.UserRegistrationView.as_view(), name='api_register'),
    path('api/home/', api_views.AppHomeView.as_view(), name='api_home'),
    path('api/courses/', api_views.CourseListView.as_view(), name='api_courses'),
    path('api/my-learning/', api_views.MyCoursesView.as_view(), name='api_my_learning'),
    path('api/profile/', api_views.UserProfileView.as_view(), name='api_profile'),
    path('api/enroll/', api_views.EnrollCourseView.as_view(), name='api_enroll'),
    path('api/change-password/', api_views.ChangePasswordView.as_view(), name='api_change_password'),
    path('api/lessons/<int:lesson_id>/complete/', mark_lesson_complete, name='mark_lesson_complete'),
    path('api/lessons/<int:lesson_id>/query/', api_views.SubmitLessonQueryView.as_view(), name='api_submit_query'),
    path('api/lessons/<int:lesson_id>/queries/list/', api_views.LessonQueryListView.as_view(), name='api_query_list'),
    path('api/notifications/', api_views.NotificationListView.as_view(), name='api_notifications'),
    path('api/notifications/<int:notification_id>/read/', api_views.mark_notification_read, name='mark_notification_read'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)