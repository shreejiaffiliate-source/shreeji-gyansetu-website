from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import MasterCategory, Course, Module, Lesson, Profile

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterCategory
        fields = ['id', 'title', 'slug', 'icon_class']

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['user_type', 'photo', 'phone_number', 'college_name', 'branch', 'is_approved']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile']

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'lesson_type', 'video_url', 'content_file', 'is_preview', 'order']

class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    class Meta:
        model = Module
        fields = ['id', 'title', 'order', 'lessons']

class CourseSerializer(serializers.ModelSerializer):
    master_category = CategorySerializer(read_only=True)
    teacher = UserSerializer(read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)
    enrollment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'thumbnail', 'description', 
            'price', 'discount_price', 'level', 'is_live', 
            'master_category', 'teacher', 'enrollment_count', 'modules'
        ]