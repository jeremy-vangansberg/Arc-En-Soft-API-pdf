from celery import Celery
import os

REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_USER = os.getenv('REDIS_USER')
REDIS_HOST = os.getenv('REDIS_HOST')

celery_app = Celery(
    "worker",
    broker=f"redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:6379",
    include=["tasks"]  # Assurez-vous de mettre à jour le chemin vers vos tâches Celery
)

# Configuration optionnelle de Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Accepte le contenu JSON
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True,
)
