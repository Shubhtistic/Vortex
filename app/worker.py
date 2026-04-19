from arq import cron
from app.core.redis import REDIS_SETTINGS
# Import the function we just wrote
from app.tasks import save_batch

class WorkerSettings:
    # 1. Tell the worker where Redis lives
    redis_settings = REDIS_SETTINGS
    
    # ron jobs
    cron_jobs = [
        cron(
            save_batch, 
            # Run on the 0th, 5th, 10th, 15th... second of every minute
            second={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}
        )
    ]