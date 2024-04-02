from celery import Celery

celery_app = Celery(
    "worker",
    broker="redis://demo_redis:6379/0",
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
