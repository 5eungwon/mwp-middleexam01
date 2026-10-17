"""Copy contents into the WSGI file linked in PythonAnywhere's Web tab.
Create ~/.config/photoblog.json first; see docs/PYTHONANYWHERE.md.
"""
import json
import os
import sys
from pathlib import Path

config = json.loads((Path.home() / '.config' / 'photoblog.json').read_text())
project = Path.home() / 'mwp-middleexam01' / 'PhotoBlogServer'
sys.path.insert(0, str(project))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['DJANGO_DEBUG'] = '0'
os.environ['DJANGO_SECRET_KEY'] = config['secret_key']
os.environ['DJANGO_ALLOWED_HOSTS'] = config['hostname']
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
