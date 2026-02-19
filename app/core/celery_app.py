from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "Vortex_worker",
    broker=settings.REDIS_URL,
    # backend=settings.REDIS_URL,
    include=["app.tasks"],
)
# broker -> Where to pick up tasks (Redis)

# backend -> Where to store results (Redis)
# We have removed the backend field as it stores results of tasks. but we do not retrieve it
# now
# redis only stores pending tasks
# no result storage , less memory usage and less Redis pressure
# for high-volume telemetry, this is better


# configure/updte settings for celery
# We force JSON serialization for security (prevents code execution attacks).
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
