"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
app = application

# Inisialisasi otomatis skema database & akun bawaan jika belum ada (Serverless Vercel)
try:
    from django.db import connection
    with connection.cursor() as cursor:
        tables = connection.introspection.table_names(cursor)
        if 'accounts_user' not in tables:
            from django.core.management import call_command
            call_command('migrate', interactive=False)
            call_command('setup_cloud_db')
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Inisialisasi startup database: {e}")


