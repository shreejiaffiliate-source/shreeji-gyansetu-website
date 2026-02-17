from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.exceptions import NotRegistered
from .models import (
    MasterCategory, Course, Module, Lesson, 
    Carousel, SuccessStory, StudyMaterial, YouTubeChannel, Profile
)

# --- INLINES ---
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'lesson_type', 'is_preview', 'order')

class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1

# --- ADMIN CLASSES ---

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    # This search_field is what makes 'Course' highlighted in the Lesson Admin
    search_fields = ('title', 'teacher__username') 
    list_display = ('id', 'title', 'master_category_id', 'price', 'is_active', 'is_live')
    list_filter = ('master_category', 'level', 'is_live', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):

    fields = ('master_category', 'course', 'title', 'order')

    # search_fields = ('title', 'course__title')
    list_display = ('id', 'title', 'course_id', 'master_category_id', 'order')
    list_filter = ('master_category', 'course',)

    autocomplete_fields = ['master_category']

    inlines = [LessonInline]

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    # Ensure course is at the top
    fields = ('course', 'module', 'title', 'thumbnail', 'lecturer_name', 'description', 'lesson_type', 'video_url', 'content_file', 'notes_file', 'is_preview', 'order')
    list_display = ('id', 'title', 'lecturer_name', 'course_id', 'module_id', 'lesson_type', 'is_preview', 'order')
    list_filter = ('lesson_type', 'course', 'module')
    
    # Both are now searchable and highlighted
    autocomplete_fields = ['course']

# Rest of registrations
@admin.register(MasterCategory)
class MasterCategoryAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    list_display = ('id', 'title', 'order', 'slug')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Carousel)
class CarouselAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')

admin.site.register(SuccessStory)
admin.site.register(StudyMaterial)
admin.site.register(YouTubeChannel)

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'User Profiles'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_user_type')

    def get_user_type(self, obj):
        return obj.profile.user_type
    get_user_type.short_description = 'User Type'

# Re-register UserAdmin

try:
    admin.site.unregister(User)
except NotRegistered:
    pass
admin.site.register(User, UserAdmin)