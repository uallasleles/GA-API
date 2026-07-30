from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()
# from listener.config import BROKER_URL


celery_app = Celery("sync_tasks", broker=os.getenv("BROKER_URL"))
