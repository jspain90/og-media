from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.database import SessionLocal
from app.services.queue_builder import QueueBuilder
import os
from dotenv import load_dotenv

load_dotenv()

scheduler = BackgroundScheduler()

def refresh_all_queues():
    """Background job to refresh all channel queues"""
    print("Starting scheduled queue refresh...")
    db = SessionLocal()
    try:
        queue_builder = QueueBuilder(db)
        results = queue_builder.rebuild_all_queues()
        print(f"Queue refresh complete. Results: {results}")
    except Exception as e:
        print(f"Error during scheduled queue refresh: {e}")
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler"""
    refresh_interval = int(os.getenv("QUEUE_REFRESH_INTERVAL", 60))

    scheduler.add_job(
        refresh_all_queues,
        trigger=IntervalTrigger(minutes=refresh_interval),
        id="refresh_queues",
        name="Refresh all channel queues",
        replace_existing=True
    )

    scheduler.start()
    print(f"Scheduler started. Queues will refresh every {refresh_interval} minutes.")

def stop_scheduler():
    """Stop the background scheduler"""
    scheduler.shutdown()
    print("Scheduler stopped.")
