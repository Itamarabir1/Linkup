import asyncio
import logging
import signal
import sys

# Infrastructure
from app.infrastructure.rabbitmq.client import rabbit_client
from app.infrastructure.rabbitmq.consumer import RabbitMQConsumer
from app.infrastructure.events.dispacher.registry import DispatcherFactory
from app.domain.events.routing import (
    NOTIFICATION_EXCHANGES,
    AVATAR_UPLOAD_EXCHANGES,
    SCHEDULED_EXCHANGES,
    SCHEDULED_TASKS_QUEUE,
)
from app.infrastructure.events.publishers.rabbitmq import RabbitMQPublisher

from app.db import models
from app.domain.rides.model import Ride
from app.domain.users.model import User
from app.domain.bookings.model import Booking
# Workers & Tasks
from app.workers.outbox_worker import run_outbox_worker
from app.workers.tasks.notification_tasks import handle_notification_event
from app.workers.tasks.avatar_tasks import handle_avatar_upload_event
from app.workers.tasks.scheduled_tasks import (
    run_scheduled_tasks_publisher,
    handle_scheduled_task,
)

# הגדרת לוגר
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WorkerMain")

async def main():
    logger.info("🚀 Linkup Worker Engine is starting...")
    
    # 1. ניהול Graceful Shutdown - הגדרה מוקדמת
    stop_event = asyncio.Event()
    tasks = []

    def stop_handler():
        """פונקציה שתקרא בזמן פקודת עצירה"""
        logger.info("🛑 Shutdown signal received. Signalizing tasks to stop...")
        stop_event.set()

    # טיפול בסיגנלים - שבירת המוקש של Windows
    if sys.platform != "win32":
        # לינוקס / מאק תומכים ב-add_signal_handler
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_handler)
    else:
        # ב-Windows אנחנו נסמוך על KeyboardInterrupt בתוך ה-try
        logger.info("ℹ️ Windows detected: Using standard interrupt handling.")

    try:
        # 2. אתחול תשתיות
        await rabbit_client.connect()

        # 3. הזרקת תלויות (Dependency Injection)
        rmq_publisher = RabbitMQPublisher(rabbit_client=rabbit_client)
        dispatcher = DispatcherFactory.create_standard_dispatcher(publishers=[rmq_publisher])

        notifications_consumer = RabbitMQConsumer(
            rabbit_client,
            queue_name="notifications_queue",
            exchange_names=NOTIFICATION_EXCHANGES,
        )
        avatar_upload_consumer = RabbitMQConsumer(
            rabbit_client,
            queue_name="avatar_upload_queue",
            exchange_names=AVATAR_UPLOAD_EXCHANGES,
        )
        scheduled_tasks_consumer = RabbitMQConsumer(
            rabbit_client,
            queue_name=SCHEDULED_TASKS_QUEUE,
            exchange_names=SCHEDULED_EXCHANGES,
        )

        # 4. הגדרת המשימות כ-Tasks עצמאיים (כולל משימות מתוזמנות דרך התור)
        tasks = [
            asyncio.create_task(notifications_consumer.consume(callback=handle_notification_event)),
            asyncio.create_task(avatar_upload_consumer.consume(callback=handle_avatar_upload_event)),
            asyncio.create_task(scheduled_tasks_consumer.consume(callback=handle_scheduled_task)),
            asyncio.create_task(run_scheduled_tasks_publisher()),
            asyncio.create_task(run_outbox_worker(dispatcher=dispatcher)),
        ]

        logger.info(f"✅ All {len(tasks)} workers are running. Press Ctrl+C to stop.")

        # 5. המתנה לסיום - או שמישהו סימן עצירה, או שאחת המשימות קרסה
        stop_task = asyncio.create_task(stop_event.wait())
        
        # אנחנו מחכים ש-stop_event יופעל (ע"י ה-handler או ה-except)
        await stop_task

    except (KeyboardInterrupt, SystemExit):
        # תופס Ctrl+C ב-Windows
        logger.info("⌨️ Keyboard Interrupt received.")
        stop_handler()
    except Exception as e:
        logger.error(f"❌ Critical error during worker startup: {e}", exc_info=True)
    
    finally:
        # 6. ניקוי (Graceful Cleanup)
        logger.info("👋 Shutting down: Cancelling all tasks...")
        
        for t in tasks:
            if not t.done():
                t.cancel()
        
        if tasks:
            # המתנה של מקסימום 5 שניות לסגירת המשימות
            await asyncio.wait(tasks, timeout=5)
        
        # סגירת החיבור הפיזי לרביט
        await rabbit_client.close()
        logger.info("🏁 Linkup Worker Engine shut down cleanly.")

if __name__ == "__main__":
    # שימוש ב-run בצורה בטוחה
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # מונע הדפסת Traceback מכוער כשסוגרים את הטרמינל
        pass