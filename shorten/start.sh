#!/bin/bash

# запуск воркера
celery -A celery_work worker --loglevel=info -Q cleanup_queue -n cleanup_worker@%h -P eventlet

# запуск планировщика
celery -A celery_work beat --loglevel=info --scheduler redbeat.RedBeatScheduler

# запуск мониторинга flower
celery -A celery_work flower --port=5555 --broker=redis://localhost:6379/1