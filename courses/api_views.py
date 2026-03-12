from rest_framework import generics, permissions, status, decorators
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from .models import Course, MasterCategory, Notification, Profile, Carousel, Lesson, LessonQuery
from .serializers import CourseSerializer, CategorySerializer, UserSerializer, SliderSerializer
from django.db import IntegrityError
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import IsAuthenticated
import razorpay
from django.conf import settings
from django.db.models import Count

User = get_user_model()

class ApiRoot(APIView):
    def get(self, request, format=None):
        return Response({
            'login': reverse('api_token_auth', request=request, format=format),
            'register': reverse('api_register', request=request, format=format),
            'home': reverse('api_home', request=request, format=format),
            'courses': reverse('api_courses', request=request, format=format),
            'my-learning': reverse('api_my_learning', request=request, format=format),
            'profile': reverse('api_profile', request=request, format=format),
            'enroll': reverse('api_enroll', request=request, format=format),
        })

# 1. Home Screen Data (Categories + Popular Courses)
class AppHomeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        sliders = Carousel.objects.filter(is_active=True).order_by('order')
        categories = MasterCategory.objects.all().order_by('order')
        popular_courses = Course.objects.filter(is_active=True).annotate(
        num_students=Count('students')
    ).order_by('-num_students', '-id').distinct()[:5]
        
        # Create a basic response dictionary
        data = {
            "sliders": SliderSerializer(sliders, many=True, context={'request': request}).data,
            "categories": CategorySerializer(categories, many=True, context={'request': request}).data,
            "popular_courses": CourseSerializer(popular_courses, many=True, context={'request': request}).data,
            "user": None # Default for guests
        }

        # If user is logged in, attach their profile data
        if request.user.is_authenticated:
            data["user"] = UserSerializer(request.user, context={'request': request}).data
            
        return Response(data)

# 2. List All Courses / Search
class CourseListView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Start with all active courses
        queryset = Course.objects.filter(is_active=True)
        
        # Get the category_slug from the URL parameters
        category_slug = self.request.query_params.get('category_slug')
        
        if category_slug:
            # Filter by the slug of the master category
            queryset = queryset.filter(master_category__slug=category_slug)
            
        return queryset

    # Ensure context is passed for absolute video URLs
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

# 3. Student's Enrolled Courses
class MyCoursesView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        # Direct query on Course model is more efficient for progress calculation
        return Course.objects.filter(
            students=self.request.user,
            is_active=True
        ).distinct()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

# 4. User Profile Details
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        # 1. Save the basic user data (first_name, email, etc.)
        user = serializer.save()
        
        # 2. Extract profile data from the request
        # In Flutter, we sent these as 'profile.bio', etc.
        profile_data = self.request.data
        profile = user.profile
        
        # 3. Manually update the Profile fields
        profile.phone_number = profile_data.get('profile.phone_number', profile.phone_number)
        profile.branch = profile_data.get('profile.branch', profile.branch)
        profile.college_name = profile_data.get('profile.college_name', profile.college_name)
        profile.enrollment_number = profile_data.get('profile.enrollment_number', profile.enrollment_number)
        profile.qualification = profile_data.get('profile.qualification', profile.qualification)
        dob = profile_data.get('profile.date_of_birth')
        if dob and dob.strip(): # If it has a real value, save it
            profile.date_of_birth = dob
        elif dob == "": # If it's an empty string from Flutter, set to NULL
            profile.date_of_birth = None
        profile.bio = profile_data.get('profile.bio', profile.bio)
        
        # 4. Handle the Photo upload if present
        if 'profile.photo' in self.request.FILES:
            profile.photo = self.request.FILES['profile.photo']
            
        profile.save()
    
class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data  # DRF parses JSON or Form data automatically
        
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        user_type = data.get('user_type', 'Student')

        # 1. Basic Validation
        if not username or not password:
            return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 2. Create User
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )

            # 3. Update Profile (Django signals usually create the profile automatically)
            profile = user.profile
            profile.user_type = user_type
            
            if user_type == 'Teacher':
                profile.qualification = data.get('qualification', '')
                profile.experience_years = data.get('experience', '')
                profile.is_approved = False # Teachers need admin approval
            else:
                profile.is_approved = True # Students approved by default
            
            profile.save()

            return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class EnrollCourseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        course_id = request.data.get('course_id')
        try:
            course = Course.objects.get(id=course_id)
            if course.students.filter(id=request.user.id).exists():
                return Response({"message": "Already enrolled"}, status=status.HTTP_200_OK)
            
            course.students.add(request.user)
            return Response({"message": "Enrolled successfully"}, status=status.HTTP_201_CREATED)
            
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        user = request.user

        # 1. Check if old password is correct
        if not user.check_password(old_password):
            return Response({"error": "Incorrect old password"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Set and save new password
        user.set_password(new_password)
        user.save()

        # 3. Keep the user logged in after password change
        update_session_auth_hash(request, user)
        
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
    
class SubmitLessonQueryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            question_text = request.data.get('question')
            
            if not question_text:
                return Response({"error": "Question text is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Create the query linked to the student and the lesson
            LessonQuery.objects.create(
                lesson=lesson,
                student=request.user,
                question=question_text
            )
            
            return Response({"message": "Query submitted successfully"}, status=status.HTTP_201_CREATED)
            
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class LessonQueryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        # Fetch queries for this specific lesson asked by the current student
        queries = LessonQuery.objects.filter(
            lesson_id=lesson_id, 
            student=request.user
        ).order_by('-created_at')
        
        data = [{
            "id": q.id,
            "question": q.question,
            "answer": q.answer,
            "is_resolved": q.is_resolved,
            "created_at": q.created_at.strftime("%d %b, %Y")
        } for q in queries]
        
        return Response(data)
    
class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        data = [{
            "id": n.id,
            "message": n.message,
            "lesson_id": n.query.lesson.id,
            "course_title": n.query.lesson.course.title
        } for n in notifications]
        return Response(data)

@decorators.api_view(['POST']) # Add this decorator
@decorators.permission_classes([IsAuthenticated]) # Add this decorator    
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({"status": "success"})
    except Notification.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    
class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request}) # CRITICAL for last_position
        return context
    
# Initialize Razorpay Client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class EnrollCourseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        course_id = request.data.get('course_id')
        payment_id = request.data.get('razorpay_payment_id') # New field from Flutter

        if not payment_id:
            return Response({"error": "Payment ID is required"}, status=400)

        try:
            # 1. Verify Payment with Razorpay
            payment_details = client.payment.fetch(payment_id)
            
            # Check if payment is authorized/captured and amount matches
            if payment_details['status'] not in ['authorized', 'captured']:
                return Response({"error": "Payment not verified"}, status=400)

            # 2. Proceed with Enrollment
            course = Course.objects.get(id=course_id)
            if course.students.filter(id=request.user.id).exists():
                return Response({"message": "Already enrolled"}, status=200)
            
            course.students.add(request.user)
            return Response({"message": "Enrolled successfully"}, status=201)
            
        except razorpay.errors.BadRequestError:
            return Response({"error": "Invalid Payment ID"}, status=400)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
class UpdateFCMTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        fcm_token = request.data.get('fcm_token')
        if not fcm_token:
            return Response({"error": "Token is required"}, status=400)
        
        # Update the user's profile with the new token
        profile = request.user.profile
        profile.fcm_token = fcm_token
        profile.save()
        
        return Response({"message": "FCM Token updated successfully"}, status=200)