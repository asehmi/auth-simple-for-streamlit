"""
Email service for sending signup verification PINs via SendGrid.
"""

import logging
from os import environ as osenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)


class EmailService:
    """Send emails via SendGrid."""

    SENDGRID_API_KEY = osenv.get('SENDGRID_API_KEY')
    FROM_EMAIL = osenv.get('NOTIFICATION_FROM_EMAIL')

    @staticmethod
    def send_signup_pin(to_email: str, pin: str) -> bool:
        """
        Send a signup verification PIN to the user's email.

        Args:
            to_email: Recipient email address
            pin: 6-digit PIN string

        Returns:
            True if sent successfully, False otherwise
        """
        if not EmailService.SENDGRID_API_KEY or not EmailService.FROM_EMAIL:
            logger.error('SendGrid credentials not configured. Set SENDGRID_API_KEY and NOTIFICATION_FROM_EMAIL in .env')
            return False

        try:
            subject = 'Your sign-up verification code'

            # Plain text body
            text_content = f"""Your sign-up verification code is: {pin}

This code expires in 30 minutes. If you did not request this code, please ignore this email."""

            # HTML body
            html_content = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <p>Your sign-up verification code is:</p>
    <h2 style="color: #2c3e50; letter-spacing: 2px;">{pin}</h2>
    <p style="color: #7f8c8d; font-size: 14px;">
        This code expires in 30 minutes. If you did not request this code, please ignore this email.
    </p>
</body>
</html>
"""

            message = Mail(
                from_email=Email(EmailService.FROM_EMAIL),
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=Content('text/plain', text_content),
                html_content=Content('text/html', html_content),
            )

            sg = SendGridAPIClient(EmailService.SENDGRID_API_KEY)
            response = sg.send(message)

            # SendGrid returns 202 on success
            if response.status_code in (200, 201, 202):
                logger.info(f'Signup PIN sent to {to_email}')
                return True
            else:
                logger.error(f'SendGrid returned status {response.status_code}: {response.body}')
                return False

        except Exception as e:
            logger.error(f'Failed to send signup PIN email to {to_email}: {str(e)}')
            return False
