

from pathlib import Path
from datetime import timedelta
import os
import cloudinary
import dj_database_url
from dotenv import load_dotenv


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-7e$+hi!q^%fpe!wa-j+zjfxl2h&1^7lezt^bfiuid!i=@2p-17'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'
IS_PRODUCTION = not DEBUG

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Allow Render's auto-generated hostname in production
if IS_PRODUCTION:
    RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_EXTERNAL_HOSTNAME:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    # Also allow .onrender.com subdomains
    ALLOWED_HOSTS.extend(['.onrender.com'])


# Application definition

INSTALLED_APPS = [
    
    'django.contrib.admin',
    'rest_framework',
    'accounts',
    'projects',
    'corsheaders',
    'rest_framework_simplejwt.token_blacklist',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary',
    'cloudinary_storage',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]



AUTH_USER_MODEL = 'accounts.User'


cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        "accounts.authentication.CookieJWTAuthentication",
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    
    # These are the important settings for cookie-based auth
    'AUTH_COOKIE': 'access_token',  
    'AUTH_COOKIE_REFRESH': 'refresh_token',  
    'AUTH_COOKIE_SECURE': IS_PRODUCTION,  # True in prod (HTTPS required)
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_SAMESITE': 'None' if IS_PRODUCTION else 'Lax',  # None for cross-domain
    'AUTH_COOKIE_PATH': '/',
    
    # Tell SimpleJWT to check cookies for the token
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # Token settings
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}


CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

ROOT_URLCONF = 'unitrack.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'unitrack.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

_db_config = dj_database_url.config(
    default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'
)

# Run SQLite tests against an in-memory database for speed/isolation.
# Postgres/other engines are unaffected.
if _db_config.get('ENGINE') == 'django.db.backends.sqlite3':
    _db_config['TEST'] = {'NAME': ':memory:'}

DATABASES = {
    'default': _db_config,
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# ✅ FIXED CORS SETTINGS
# Allow all origins for demo/hackathon purposes
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

SESSION_COOKIE_SECURE = IS_PRODUCTION
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'None' if IS_PRODUCTION else 'Lax'

CSRF_COOKIE_SECURE = IS_PRODUCTION
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'None' if IS_PRODUCTION else 'Lax'

JWT_AUTH_COOKIE = "access_token"
JWT_AUTH_REFRESH_COOKIE = "refresh_token"


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
