import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "django-insecure-y4z+pv#*#p9rg&(@*qaopp_4$s5^j02&_)pa(p-_ui+5&gl3&v"
DEBUG = True
ALLOWED_HOSTS = ["*", "www.gyansetu.shreejifintech.com"]

CSRF_TRUSTED_ORIGINS = [
    "https://www.gyansetu.shreejifintech.com"
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django.contrib.sites',
    "users",
    "courses",
    "smart_selects",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "courses.context_processors.extras",
                "courses.context_processors.unread_notifications",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True

# settings.py
DATETIME_FORMAT = "d M Y, P"  # e.g., 21 Feb 2026, 12:40 p.m.
USE_L10N = False  # Make Django use your DATETIME_FORMAT instead of locale default
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR / "static")
    ]
STATIC_ROOT = os.path.join(BASE_DIR / "staticfiles")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User Model
AUTH_USER_MODEL = 'users.User'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR / 'media')

USE_DJANGO_JQUERY = True

LOGIN_REDIRECT_URL = 'login_success'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = '/login/'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = ('shreejiaffiliate@gmail.com')
EMAIL_HOST_PASSWORD = ('cqalsnvodeavhxxa')
DEFAULT_FROM_EMAIL = ('Shreeji GyanSetu <shreejiaffiliate@gmail.com>')

CORS_ALLOW_ALL_ORIGINS = True # Allow all devices (Flutter app, Emulator, etc.)
CORS_ALLOW_CREDENTIALS = True

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# Razorpay Configuration
RAZORPAY_KEY_ID = 'rzp_test_SOCWZ8L1q01O7W'  # Replace with your actual Key ID
RAZORPAY_KEY_SECRET = '5TdpyMGMMCIlOPu69YoW61Zs'  # Replace with your actual Secret Key

# It's good practice to toggle between Test and Live modes here
RAZORPAY_IS_LIVE = False

GOOGLE_OAUTH2_CLIENT_ID = '305890739233-vl7frn1tvpo8kigp17aost7ffa86aidh.apps.googleusercontent.com'

# Allauth settings
ACCOUNT_EMAIL_VERIFICATION = "none" # Kyunki hum apna custom OTP logic use kar rahe hain
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True

# Agar aap chahte ho ki Google se login ke baad direct dashboard jaye
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_LOGIN_ON_GET = True # Isse confirmation page skip ho jayega direct login hoga

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

# Isse login failure ka asli error message terminal mein dikhega
SOCIALACCOUNT_ADAPTER = 'courses.adapters.MySocialAccountAdapter'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
