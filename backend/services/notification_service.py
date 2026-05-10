"""
Notification Service

Handles sending notifications when batch jobs complete.
Supports email notifications and in-app notifications.
"""
import os
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    email_enabled: bool = False
    email_address: Optional[str] = None
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None


class NotificationService:
    """Service for sending notifications."""
    
    def __init__(self):
        self.config = NotificationConfig()
        # Load config from environment variables
        self.config.email_enabled = os.getenv("NOTIFICATION_EMAIL_ENABLED", "false").lower() == "true"
        self.config.email_address = os.getenv("NOTIFICATION_EMAIL_ADDRESS")
        self.config.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.config.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.config.smtp_username = os.getenv("SMTP_USERNAME")
        self.config.smtp_password = os.getenv("SMTP_PASSWORD")
    
    def send_batch_completion_notification(
        self,
        project_title: str,
        chapters_completed: int,
        total_chapters: int,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Send notification when batch job completes.
        
        Args:
            project_title: Name of the audiobook project
            chapters_completed: Number of chapters processed
            total_chapters: Total number of chapters
            success: Whether the batch job succeeded
            error_message: Error message if failed
            
        Returns:
            True if notification was sent successfully
        """
        if not self.config.email_enabled or not self.config.email_address:
            logger.info("Email notifications not enabled")
            return False
        
        try:
            if success:
                subject = f"Audiobook Complete: {project_title}"
                body = f"""
Your audiobook "{project_title}" has been successfully processed.

Summary:
- Chapters completed: {chapters_completed}/{total_chapters}
- Status: Success

You can now export your audiobook from the application.
"""
            else:
                subject = f"Audiobook Failed: {project_title}"
                body = f"""
Your audiobook "{project_title}" processing failed.

Summary:
- Chapters completed: {chapters_completed}/{total_chapters}
- Status: Failed
- Error: {error_message}

Please check the application for more details.
"""
            
            # Try to send email
            return self._send_email(self.config.email_address, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def _send_email(self, to_address: str, subject: str, body: str) -> bool:
        """
        Send email using SMTP.
        
        Args:
            to_address: Recipient email address
            subject: Email subject
            body: Email body
            
        Returns:
            True if email was sent successfully
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_username or "audiobook-maker@noreply.com"
            msg['To'] = to_address
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                if self.config.smtp_username and self.config.smtp_password:
                    server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_address}")
            return True
            
        except ImportError:
            logger.warning("SMTP libraries not available")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Check if notifications are enabled."""
        return self.config.email_enabled and bool(self.config.email_address)


# Singleton instance
notification_service = NotificationService()
