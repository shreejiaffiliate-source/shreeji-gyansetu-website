from django.db import models
from django.utils.text import slugify
from smart_selects.db_fields import ChainedForeignKey

class MasterCategory(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon_class = models.CharField(max_length=50, default="fa-book")
    order = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "1. Master Categories"
        ordering = ['order']
    def __str__(self): return self.title

class Course(models.Model):
    LEVEL_CHOICES = [('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')]
    master_category = models.ForeignKey(MasterCategory, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/')
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='Beginner')
    is_live = models.BooleanField(default=False)
    enrollment_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "2. Courses"
    def __str__(self): return self.title

class Carousel(models.Model):
    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to='carousels/')
    link = models.URLField(blank=True, help_text="Link to a course or page")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "0. Homepage Sliders"
        ordering = ['order']
    def __str__(self): return self.title

class Module(models.Model):
    # Changed related_name to 'category_modules' to avoid conflict with Course
    master_category = models.ForeignKey(MasterCategory, on_delete=models.CASCADE, related_name='category_modules')

    # Added related_name='modules' to fix AttributeError at /course/
    course = ChainedForeignKey(
        Course,
        chained_field="master_category",
        chained_model_field="master_category",
        show_all=False,
        auto_choose=True,
        sort=True,
        related_name='modules'
    )

    title = models.CharField(max_length=200) 
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "3. Modules" 
        ordering = ['order']

    def __str__(self): 
        return f"{self.course.title} - {self.title}"

class Lesson(models.Model):
    LESSON_TYPES = [('Video', 'Video'), ('PDF', 'Notes'), ('Quiz', 'Quiz')]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_lessons')
    
    # related_name='lessons' fixes AttributeError in course_detail
    module = ChainedForeignKey(
        Module,
        chained_field="course",
        chained_model_field="course",
        show_all=False,
        auto_choose=True,
        sort=True,
        related_name='lessons'
    )
    
    title = models.CharField(max_length=200)
    lesson_type = models.CharField(max_length=10, choices=LESSON_TYPES, default='Video')
    video_url = models.URLField(blank=True, null=True, help_text="YouTube or Vimeo Link")
    content_file = models.FileField(upload_to='lessons/', blank=True, null=True)
    is_preview = models.BooleanField(default=False, help_text="Check if this is a free demo lesson")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "4. Lessons"
        ordering = ['order']

    def __str__(self): 
        return f"{self.module.title} - {self.title}"

class StudyMaterial(models.Model):
    title = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=50, default="fa-file-pdf")
    link = models.URLField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "5. Study Materials"
        ordering = ['order']
    def __str__(self): return self.title

class SuccessStory(models.Model):
    name = models.CharField(max_length=100)
    exam_name = models.CharField(max_length=100)
    rank = models.CharField(max_length=20)
    image = models.ImageField(upload_to='success_stories/')
    short_bio = models.TextField()

    class Meta:
        verbose_name_plural = "6. Success Stories"
    def __str__(self): return f"{self.name} ({self.rank})"

class YouTubeChannel(models.Model):
    name = models.CharField(max_length=100)
    subscribers = models.CharField(max_length=20)
    channel_url = models.URLField()

    class Meta:
        verbose_name_plural = "7. YouTube Channels"
    def __str__(self): return self.name