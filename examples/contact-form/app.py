"""
Minimal Django setup for Contact Form example.

Run with: python app.py
"""

import os
import sys
from pathlib import Path

import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import path, include

# Get the directory containing this file
BASE_DIR = Path(__file__).resolve().parent

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='django-insecure-contact-form-example-key',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'nitro',
        ],
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [BASE_DIR],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                ],
            },
        }],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        USE_TZ=True,
        # Nitro configuration
        NITRO={
            'SECRET_KEY': 'nitro-example-secret-key',
        },
    )

django.setup()

# Import component after Django is configured
from component import ContactForm  # noqa: E402


def contact_form_view(request):
    """Render the contact form page."""
    component = ContactForm(request)
    return HttpResponse(render_to_string('template.html', {
        'contact_form': component.render()
    }))


# URL Configuration
urlpatterns = [
    path('', contact_form_view, name='contact_form'),
    path('nitro/', include('nitro.urls')),
]

if __name__ == '__main__':
    # Run the development server
    if len(sys.argv) == 1:
        sys.argv.append('runserver')
    execute_from_command_line(sys.argv)
