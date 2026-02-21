"""
ASGI config for barsuk_admin project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barsuk_admin.settings')

application = get_asgi_application()