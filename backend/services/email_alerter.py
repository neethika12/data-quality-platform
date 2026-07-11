import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime

class EmailAlerter:
    """Send email notifications for critical alerts."""

    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = None
        self.sender_password = None

    def configure(self, email: str, password: str):
        """Configure email credentials."""
        self.sender_email = email
        self.sender_password = password

    def send_alert(self, recipient_email: str, dataset_name: str, alerts: List[dict],
                   quality_score: float) -> bool:
        """Send email alert for quality issues."""
        if not self.sender_email or not self.sender_password:
            return False

        try:
            # Create message
            subject = f"🚨 Data Quality Alert: {dataset_name}"
            html_body = self._generate_html_body(dataset_name, alerts, quality_score)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = recipient_email

            msg.attach(MIMEText(html_body, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, msg.as_string())

            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def send_summary_report(self, recipient_email: str, dataset_name: str,
                          summary: dict) -> bool:
        """Send daily/weekly summary report."""
        if not self.sender_email or not self.sender_password:
            return False

        try:
            subject = f"📊 Data Quality Report: {dataset_name}"
            html_body = self._generate_summary_html(dataset_name, summary)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = recipient_email

            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, msg.as_string())

            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    @staticmethod
    def _generate_html_body(dataset_name: str, alerts: List[dict], quality_score: float) -> str:
        """Generate HTML email body for alerts."""
        critical_alerts = [a for a in alerts if a.get("severity") == "CRITICAL"]
        warning_alerts = [a for a in alerts if a.get("severity") == "WARNING"]

        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #e74c3c;">🚨 Data Quality Alert</h2>

                    <p>Quality issues detected in <strong>{dataset_name}</strong></p>

                    <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #e74c3c; margin: 20px 0;">
                        <h3>Quality Score: {quality_score:.1%}</h3>
                        <p style="color: #e74c3c; font-weight: bold;">Status: ❌ ACTION REQUIRED</p>
                    </div>

                    <h3 style="color: #e74c3c;">Critical Issues ({len(critical_alerts)})</h3>
                    <ul>
        """

        for alert in critical_alerts[:5]:
            html += f"""
                        <li>
                            <strong>{alert.get('metric_type', 'Unknown')}</strong>: {alert.get('message', '')}
                            <br/>Value: {alert.get('value', 'N/A')} | Threshold: {alert.get('threshold', 'N/A')}
                        </li>
            """

        html += """
                    </ul>

                    <h3 style="color: #f39c12;">Warnings ({})
                    </h3>
                    <ul>
        """.format(len(warning_alerts))

        for alert in warning_alerts[:3]:
            html += f"""
                        <li>
                            <strong>{alert.get('metric_type', 'Unknown')}</strong>: {alert.get('message', '')}
                        </li>
            """

        html += """
                    </ul>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                    <p style="color: #7f8c8d; font-size: 12px;">
                        This is an automated alert. Please log in to the dashboard for detailed analysis.
                        <br/>
                        <strong>Dashboard URL:</strong> <a href="http://localhost:8501">http://localhost:8501</a>
                    </p>

                    <p style="color: #95a5a6; font-size: 10px;">
                        Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </p>
                </div>
            </body>
        </html>
        """

        return html

    @staticmethod
    def _generate_summary_html(dataset_name: str, summary: dict) -> str:
        """Generate HTML for summary report."""
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2980b9;">📊 Data Quality Report</h2>

                    <p>Here's your data quality summary for <strong>{dataset_name}</strong></p>

                    <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #2980b9; margin: 20px 0;">
                        <h3>Key Metrics</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px;">Quality Score:</td>
                                <td style="padding: 8px; font-weight: bold;">{summary.get('quality_score', 0):.1%}</td>
                            </tr>
                            <tr style="background-color: #f0f0f0;">
                                <td style="padding: 8px;">Completeness:</td>
                                <td style="padding: 8px; font-weight: bold;">{summary.get('completeness', 0):.1%}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px;">Drift Score:</td>
                                <td style="padding: 8px; font-weight: bold;">{summary.get('drift_score', 0):.2f}</td>
                            </tr>
                            <tr style="background-color: #f0f0f0;">
                                <td style="padding: 8px;">Total Alerts:</td>
                                <td style="padding: 8px; font-weight: bold;">{summary.get('total_alerts', 0)}</td>
                            </tr>
                        </table>
                    </div>

                    <h3>Alert Summary</h3>
                    <p>
                        🔴 Critical: {summary.get('critical_count', 0)} |
                        🟡 Warnings: {summary.get('warning_count', 0)} |
                        🔵 Info: {summary.get('info_count', 0)}
                    </p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                    <p style="color: #7f8c8d; font-size: 12px;">
                        <strong>Dashboard URL:</strong> <a href="http://localhost:8501">http://localhost:8501</a>
                    </p>

                    <p style="color: #95a5a6; font-size: 10px;">
                        Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </p>
                </div>
            </body>
        </html>
        """

        return html
