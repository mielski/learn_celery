"""
this is the main script used to test celery tasks.
make sure celery is running, see readme
"""
from celery import Celery
import os

# broker = os.environ.get('CELERY_BROKER_URL', 'redis://')
# backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://')

celery_app = Celery('learn_celery', include=["tasks"])
celery_app.autodiscover_tasks()