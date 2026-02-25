from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from .models import Course, MasterCategory, Profile
from .serializers import CourseSerializer, CategorySerializer, UserSerializer

class ApiRoot(APIView):
    def get(self, request, format=None):
        return Response({
            'login': reverse('api_token_auth', request=request, format=format),
            'home': reverse('api_home', request=request, format=format),
            'courses': reverse('api_courses', request=request, format=format),
            'my-learning': reverse('api_my_learning', request=request, format=format),
            'profile': reverse('api_profile', request=request, format=format),
        })

# 1. Home Screen Data (Categories + Popular Courses)
class AppHomeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categories = MasterCategory.objects.all().order_by('order')
        popular_courses = Course.objects.filter(is_active=True).order_by('-students')[:5]
        
        return Response({
            "categories": CategorySerializer(categories, many=True).data,
            "popular_courses": CourseSerializer(popular_courses, many=True).data
        })

# 2. List All Courses / Search
class CourseListView(generics.ListAPIView):
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]

# 3. Student's Enrolled Courses
class MyCoursesView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.enrolled_courses.all()

# 4. User Profile Details
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user