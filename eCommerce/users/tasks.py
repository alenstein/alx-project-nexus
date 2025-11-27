from celery import shared_task
from django.core.mail import send_mail
from smtplib import SMTPException

@shared_task(bind=True, max_retries=3, default_retry_delay=60)  # Retry every 60 seconds
def send_confirmation_email_task(self, subject, message, from_email, recipient_list):
    """
    A Celery task to send an email asynchronously.
    It will automatically retry on SMTP errors.
    """
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    except SMTPException as exc:
        # The 'self.retry' method will re-run the task.
        # The 'exc' argument logs the exception for debugging.
        self.retry(exc=exc)
