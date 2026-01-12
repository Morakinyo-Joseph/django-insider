from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.conf import settings as django_settings
import logging

logger = logging.getLogger(__name__)

class EmailManager:
    """
    Handles sending Insider email reports using Django's email backend.
    """
    
    def __init__(self, recipients=None):
        from insider.settings import settings as insider_settings
        self.recipients = recipients or insider_settings.DAILY_REPORT_EMAILS
        self.sender = getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'insider@noreply.com')

    def send_daily_report(self, stats_context):
        """
        Sends the summary report.
        stats_context: Dict containing 'new_errors', 'total_requests', 'top_offenders', etc.
        """

        if not self.recipients:
            logger.warning("INSIDER: Daily report enabled but no recipients configured.")
            return

        subject = f"[Insider] Daily Stability Report - {stats_context['date']}"
        
        html_message = self._build_html_report(stats_context)
        plain_message = strip_tags(html_message)

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=self.sender,
                recipient_list=self.recipients,
                fail_silently=False,
            )
            logger.info(f"INSIDER: Daily report sent to {len(self.recipients)} recipients.")
        except Exception as e:
            logger.error(f"INSIDER: Failed to send email report: {e}")

    def _build_html_report(self, ctx):
        """
        Generates the HTML string for the email.
        """
        
        # Minimalist inline CSS for email compatibility
        return f"""
        <html>
        <body style="font-family: sans-serif; color: #333;">
            <div style="padding: 20px; background-color: #f4f4f5;">
                <div style="background: white; padding: 20px; border-radius: 8px; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #4f46e5; margin-top: 0;">Insider Daily Summary</h2>
                    <p style="color: #666;">Here is the stability overview for <strong>{ctx['date']}</strong>.</p>
                    
                    <div style="display: flex; gap: 10px; margin: 20px 0;">
                        <div style="flex: 1; background: #fee2e2; padding: 10px; border-radius: 4px; text-align: center;">
                            <strong style="font-size: 24px; color: #991b1b;">{ctx['errors_500']}</strong><br>
                            <span style="font-size: 12px; color: #991b1b;">Server Errors</span>
                        </div>
                        <div style="flex: 1; background: #fef3c7; padding: 10px; border-radius: 4px; text-align: center;">
                            <strong style="font-size: 24px; color: #92400e;">{ctx['new_issues']}</strong><br>
                            <span style="font-size: 12px; color: #92400e;">New Incidences</span>
                        </div>
                        <div style="flex: 1; background: #ecfccb; padding: 10px; border-radius: 4px; text-align: center;">
                            <strong style="font-size: 24px; color: #3f6212;">{ctx['resolved']}</strong><br>
                            <span style="font-size: 12px; color: #3f6212;">Resolved</span>
                        </div>
                    </div>

                    <h3 style="border-bottom: 1px solid #eee; padding-bottom: 10px;">Top Offenders</h3>
                    <ul style="padding-left: 20px;">
                        {''.join([f"<li><strong>{i['title']}</strong> - {i['count']} events</li>" for i in ctx['top_offenders']])}
                    </ul>
                    
                    <p style="font-size: 12px; color: #aaa; margin-top: 30px; text-align: center;">
                        Powered by Insider Observability
                    </p>
                </div>
            </div>
        </body>
        </html>
        """