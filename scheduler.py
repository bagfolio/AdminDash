import logging
from datetime import datetime, timedelta
from app import db
from models import ScheduledTask, APIEndpoint
from fmp_api import fetch_endpoint_data

logger = logging.getLogger(__name__)

def register_jobs(scheduler):
    """
    Register scheduled jobs with APScheduler
    
    Args:
        scheduler: APScheduler instance
    """
    # Get all active scheduled tasks
    tasks = ScheduledTask.query.filter_by(active=True).all()
    
    for task in tasks:
        schedule_task(task, scheduler)


def schedule_task(task, scheduler=None):
    """
    Schedule a task with APScheduler
    
    Args:
        task (ScheduledTask): The task to schedule
        scheduler: Optional scheduler instance (uses app.scheduler by default)
    """
    from app import scheduler as app_scheduler
    
    if scheduler is None:
        scheduler = app_scheduler
    
    # Get the endpoint for this task
    endpoint = APIEndpoint.query.get(task.endpoint_id)
    if not endpoint:
        logger.error(f"Endpoint not found for task {task.id}")
        return
    
    # Define the job function
    def job_function():
        logger.info(f"Executing scheduled task: {task.name}")
        
        try:
            # Update task's last run time
            task.last_run = datetime.utcnow()
            
            # Fetch data
            result = fetch_endpoint_data(endpoint, task.parameters)
            
            # Update next run time based on frequency
            if task.frequency == 'daily':
                task.next_run = datetime.utcnow() + timedelta(days=1)
            elif task.frequency == 'weekly':
                task.next_run = datetime.utcnow() + timedelta(days=7)
            elif task.frequency == 'monthly':
                task.next_run = datetime.utcnow() + timedelta(days=30)
            
            db.session.commit()
            
            logger.info(f"Task {task.name} completed successfully")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error executing task {task.id}: {e}")
    
    # Schedule based on frequency
    if task.frequency == 'daily':
        job = scheduler.add_job(
            job_function,
            'interval',
            days=1,
            id=f"task_{task.id}",
            replace_existing=True
        )
    elif task.frequency == 'weekly':
        job = scheduler.add_job(
            job_function,
            'interval',
            weeks=1,
            id=f"task_{task.id}",
            replace_existing=True
        )
    elif task.frequency == 'monthly':
        job = scheduler.add_job(
            job_function,
            'interval',
            days=30,
            id=f"task_{task.id}",
            replace_existing=True
        )
    
    # Execute immediately if this is a new task
    if not task.last_run:
        scheduler.add_job(
            job_function,
            'date',
            run_date=datetime.now() + timedelta(seconds=5),
            id=f"task_{task.id}_immediate"
        )
    
    logger.info(f"Scheduled task {task.id}: {task.name} with frequency {task.frequency}")


def remove_task(task, scheduler=None):
    """
    Remove a scheduled task
    
    Args:
        task (ScheduledTask): The task to remove
        scheduler: Optional scheduler instance
    """
    from app import scheduler as app_scheduler
    
    if scheduler is None:
        scheduler = app_scheduler
    
    try:
        scheduler.remove_job(f"task_{task.id}")
        logger.info(f"Removed scheduled task {task.id}: {task.name}")
    except Exception as e:
        logger.warning(f"Error removing task {task.id} from scheduler: {e}")
