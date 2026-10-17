"""WSGI configuration for the isolated PythonAnywhere v2 deployment.

Copy to the WSGI file linked in the Web tab. Configuration and secrets stay
outside the repository in ~/.config/photoblog-v2.json.
"""
import json
import os
import sys
from pathlib import Path

config = json.loads((Path.home() / '.config' / 'photoblog-v2.json').read_text())
sys.path.insert(0, config['project'])
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['DJANGO_DEBUG'] = '0'
os.environ['DJANGO_SECRET_KEY'] = config['secret_key']
os.environ['DJANGO_ALLOWED_HOSTS'] = config['hostname']
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
