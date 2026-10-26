import smtplib
from email.mime.text import MIMEText

# syslog is Unix-only; provide a fallback for Windows
try:
    import syslog
    SYSLOG_AVAILABLE = True
except ImportError:
    SYSLOG_AVAILABLE = False

class AlertManager:
    def __init__(self, config):
        self.syslog_enabled = config['alerts'].get('syslog', False) and SYSLOG_AVAILABLE
        self.email_config = config['alerts'].get('email', {})

    def send_alert(self, message, event_type='ALERT'):
        # Syslog alert (only if available and enabled)
        if self.syslog_enabled:
            try:
                syslog.syslog(syslog.LOG_ALERT, f"FIM {event_type}: {message}")
            except Exception as e:
                print(f"Failed to send syslog alert: {e}")

        # Email alert
        if self.email_config.get('enabled', False):
            self._send_email(message, event_type)

    def _send_email(self, message, event_type):
        try:
            subject = self.email_config.get('subject_prefix', '') + f" {event_type}"
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.email_config['from_addr']
            msg['To'] = self.email_config['to_addr']

            with smtplib.SMTP(self.email_config['smtp_server'],
                              self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['username'],
                             self.email_config['password'])
                server.send_message(msg)
        except Exception as e:
            print(f"Email alert failed: {e}")