import logging
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .base import BaseIntegration


logger = logging.getLogger(__name__)

class GmailIntegration(BaseIntegration):
    identifier = "gmail"
    logo_url = "https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg"
    
    config_definition = {
        "sender_email": {
            "label": "Sender Email Address",
            "type": "STRING",
            "required": True,
            "help_text": "The Gmail address sending the alert."
        },
        "app_password": { # TODO: Hash sensitive data before saving to db.
            "label": "App Password",
            "type": "PASSWORD",
            "required": True,
            "help_text": "Enable 2FA on Google and generate an App Password."
        },
        "recipient_email": {
            "label": "Recipient Email(s)",
            "type": "STRING",
            "required": True,
            "help_text": "Comma-separated list of people to notify."
        }
    }

    def run(self, footprint, context):
        config = self.get_config()
        
        sender_email = config.get("sender_email")
        password = config.get("app_password")
        recipients_str = config.get("recipient_email")

        if not (sender_email and password and recipients_str):
            logger.warning("INSIDER: Gmail integration missing required config.")
            return

        recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]

        message = MIMEMultipart("alternative")
        
        subject_title = f"Error {footprint.status_code}"
        if hasattr(footprint, 'incidence') and footprint.incidence:
             subject_title = footprint.incidence.title

        message["Subject"] = f"[Insider Alert] {subject_title}"
        message["From"] = sender_email
        message["To"] = ", ".join(recipients)

        # Check if previous integrations added context (like a Jira/GitHub link)
        extra_links = ""
        if "github_issue_url" in context:
            extra_links += f'<p><strong>GitHub Issue:</strong> <a href="{context["github_issue_url"]}">{context["github_issue_url"]}</a></p>'
        if "jira_ticket_key" in context:
             extra_links += f'<p><strong>Jira Ticket:</strong> {context["jira_ticket_key"]}</p>'

        html_content = f"""
        <html>
          <body>
            <h2 style="color: #d32f2f;">Insider Exception Alert</h2>
            <p><strong>Request:</strong> {footprint.request_method} {footprint.request_path}</p>
            <p><strong>Status:</strong> {footprint.status_code}</p>
            <p><strong>User:</strong> {footprint.request_user or 'Anonymous'}</p>
            
            {extra_links}
            
            <hr>
            <h3>Stack Trace</h3>
            <pre style="background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto;">
            {self._format_stack_trace(footprint)}
            </pre>
          </body>
        </html>
        """

        message.attach(MIMEText(html_content, "html"))

        # Send via SMTP_SSL
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, recipients, message.as_string())
            
            logger.info(f"INSIDER: Sent email alert to {len(recipients)} recipients.")
            return {"email_sent": True}

        except Exception as e:
            logger.error(f"INSIDER: Gmail send failed: {e}")
            return {}

    def _format_stack_trace(self, footprint):
        """
        Helper to extract a clean string from the stack trace list.
        """
        
        if not footprint.stack_trace:
            return "No stack trace available."
        
        if isinstance(footprint.stack_trace, str):
            return footprint.stack_trace

        lines = []
        for frame in footprint.stack_trace:
            func = frame.get('function') if isinstance(frame, dict) else frame.function
            line = frame.get('line') if isinstance(frame, dict) else frame.line
            code = frame.get('code', '').strip() if isinstance(frame, dict) else frame.code.strip()
            lines.append(f"{frame.get('file')}:{line} in {func}\n    {code}")
        
        return "\n".join(lines)