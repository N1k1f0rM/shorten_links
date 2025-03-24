from celery import Celery
from celery.schedules import crontab
from sqlalchemy import delete, select, update
from database import async_session_maker, Link, sync_session_maker
from redis import Redis
from datetime import datetime
import os
import logging


REDIS_CACHE_DB = 0
REDIS_CELERY_DB = 1


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


celery = Celery(__name__)
celery.conf.update(
    broker_url=f"redis://localhost:6379/{REDIS_CELERY_DB}",
    result_backend=f"redis://localhost:6379/{REDIS_CELERY_DB}",
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Europe/Moscow',
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_default_queue='default',
    task_queues={
        'cleanup_queue': {
            'exchange': 'cleanup',
            'routing_key': 'cleanup',
        }
    }
)


@celery.task(
    name="cleanup_task",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={'max_retries': 3},
    queue='cleanup_queue'
)
def cleanup_expired_links(self):
    try:
        logger.info("Starting periodic cleanup task...")


        with sync_session_maker() as session:

            expired_links = session.execute(
                select(Link).where(
                    Link.expires_at < datetime.now(),
                    Link.short_url.isnot(None)))

            for link in expired_links:
                link.short_url=None
            session.commit()

            redis_cache = Redis.from_url(f"redis://localhost:6379/{REDIS_CACHE_DB}")
            redis_celery = Redis.from_url(f"redis://localhost:6379/{REDIS_CELERY_DB}")

            for link in expired_links:
                redis_cache.delete(f"cache:{link.short_url}")
                redis_cache.delete(f"clicks:{link.short_url}")


            logger.info(f"Cleaned {len(expired_links)} expired links")
            return {
                "status": "success",
                "cleaned_links": len(expired_links),
                "details": [link.id for link in expired_links]
            }

    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise self.retry(exc=e, countdown=60)


celery.conf.beat_schedule = {
    '15min-cleanup': {
        'task': 'cleanup_task',
        'schedule': crontab(minute='*/1'),
        'options': {'queue': 'cleanup_queue'}
    },
}