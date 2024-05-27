from celery import Celery
from datetime import timedelta
import os

# write your celery code

os.environ.setdefault('DJANGO_SETTING_MODULE','A.settings')
celery_app = Celery(A)
celery_app.autodiscover_tasks()
