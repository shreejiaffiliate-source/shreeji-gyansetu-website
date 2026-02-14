"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib import admin
from courses.views import home, category_detail, course_detail, lesson_detail, search, teacher_dashboard,upload_course, manage_curriculum, login_required, login_success, add_lesson, register, course_detail_edit, edit_course, edit_lesson, delete_lesson
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

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
    path('dashboard/teacher/', teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/teacher/upload', upload_course, name='upload_course'),
    path('course/<slug:course_slug>/manage-curriculum/', manage_curriculum, name='manage_curriculum'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('login-success/', login_success, name='login_success'),
    path('module/<int:module_id>/add-lesson/', add_lesson, name='add_lesson'),
    path('register/', register, name='register'),
    path('course/<slug:slug>/manage', course_detail_edit, name='course_detail_edit'),
    path('course/<slug:slug>/edit', edit_course, name='edit_course'),
    path('lesson/<int:lesson_id>/edit/', edit_lesson, name='edit_lesson'),
    path('lesson/<int:lesson_id>/delete/', delete_lesson, name='delete_lesson'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
