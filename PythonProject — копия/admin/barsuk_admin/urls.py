"""
URL configuration for barsuk_admin project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from barsuk_app import views

urlpatterns = [
    # НАШ КАСТОМНЫЙ URL - ДОЛЖЕН БЫТЬ ПЕРВЫМ!
    path('admin/reply-to-request/<int:request_id>/', views.reply_to_request_view, name='reply_to_request'),

    # СТАНДАРТНЫЕ URL АДМИНКИ
    path('admin/', admin.site.urls),
]

# Добавляем обработку медиа-файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)