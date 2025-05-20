import time
from celery import shared_task
import logging


logger = logging.getLogger(__name__)

@shared_task()
def call_background_task(message):
    try:
        time.sleep(10)
        print(f"Background Task called!")
        print(message)
        return message
    except Exception as e:
        logger.error(f"Error in call_background_task: {e}")
        raise