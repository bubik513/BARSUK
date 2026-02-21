import os
from pathlib import Path

# Базовый путь
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ (в продакшене нужно вынести в .env)
SECRET_KEY = 'Afrika124578'

# Режим отладки
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Приложения
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Сторонние приложения
    'import_export',
    'rangefilter',

    # Наше приложение
    'barsuk_app',
]

# Промежуточные слои
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'barsuk_admin.urls'

# Шаблоны
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'barsuk_admin.wsgi.application'

# База данных (та же самая PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'barsuk_db',
        'USER': 'postgres',
        'PASSWORD': 'Afrika124578',  # тот же что в .env бота
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Пароли
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

# Локализация
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True
USE_L10N = False

# Форматы даты и времени для России
DATE_FORMAT = 'd E Y'  # 15 февраля 2026
DATETIME_FORMAT = 'd E Y H:i'  # 15 февраля 2026 14:30
TIME_FORMAT = 'H:i'

# Форматы для ввода дат
DATE_INPUT_FORMATS = ['%d.%m.%Y', '%d.%m.%y', '%Y-%m-%d']
DATETIME_INPUT_FORMATS = [
    '%d.%m.%Y %H:%M:%S', '%d.%m.%Y %H:%M', '%d.%m.%Y',
    '%d.%m.%y %H:%M:%S', '%d.%m.%y %H:%M', '%d.%m.%y',
    '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'
]

# Первый день недели: 0 - воскресенье, 1 - понедельник (для России)
FIRST_DAY_OF_WEEK = 1

# Разделители
DECIMAL_SEPARATOR = ','
THOUSAND_SEPARATOR = ' '  # неразрывный пробел
USE_THOUSAND_SEPARATOR = True

# Статика
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Медиа
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Логин
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'

# Настройки импорта/экспорта
IMPORT_EXPORT_USE_TRANSACTIONS = True