"""
Email service for sending store credentials to users.
Uses Gmail SMTP via App Password for reliable delivery.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def _build_html_body(
    store_name: str,
    store_type: str,
    store_url: str,
    admin_url: str,
    admin_user: str,
    admin_password: str,
    db_password: str,
    extra: dict | None = None,
) -> str:
    """Build a styled HTML email body with the store credentials."""

    extra_rows = ""
    if extra:
        for key, value in extra.items():
            label = key.replace("_", " ").title()
            extra_rows += f"""
            <tr>
              <td style="padding:10px 14px;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">{label}</td>
              <td style="padding:10px 14px;color:#111827;border-bottom:1px solid #e5e7eb;font-family:'Courier New',monospace;">{value}</td>
            </tr>"""

    return f"""
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px 40px;text-align:center;">
            <h1 style="margin:0;color:#ffffff;font-size:24px;">🎉 Your Store is Ready!</h1>
            <p style="margin:8px 0 0;color:#e0e7ff;font-size:14px;">Store &ldquo;{store_name}&rdquo; has been provisioned successfully.</p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:32px 40px;">
            <p style="color:#374151;font-size:15px;line-height:1.6;">
              Hello! Your <strong>{store_type}</strong> store is live. Below are your credentials &mdash;
              <span style="color:#dc2626;font-weight:600;">please save them securely</span>.
            </p>

            <!-- Credentials table -->
            <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
              <tr style="background:#f9fafb;">
                <th style="padding:10px 14px;text-align:left;color:#6b7280;font-size:13px;border-bottom:1px solid #e5e7eb;" width="40%">Field</th>
                <th style="padding:10px 14px;text-align:left;color:#6b7280;font-size:13px;border-bottom:1px solid #e5e7eb;">Value</th>
              </tr>
              <tr>
                <td style="padding:10px 14px;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">Store URL</td>
                <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb;">
                  <a href="{store_url}" style="color:#6366f1;text-decoration:none;">{store_url}</a>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 14px;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">Admin Panel</td>
                <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb;">
                  <a href="{admin_url}" style="color:#6366f1;text-decoration:none;">{admin_url}</a>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 14px;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">Admin Username</td>
                <td style="padding:10px 14px;color:#111827;border-bottom:1px solid #e5e7eb;font-family:'Courier New',monospace;">{admin_user}</td>
              </tr>
              <tr>
                <td style="padding:10px 14px;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">Admin Password</td>
                <td style="padding:10px 14px;color:#111827;border-bottom:1px solid #e5e7eb;font-family:'Courier New',monospace;">{admin_password}</td>
              </tr>
              <tr>
                <td style="padding:10px 14px;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">Database Password</td>
                <td style="padding:10px 14px;color:#111827;border-bottom:1px solid #e5e7eb;font-family:'Courier New',monospace;">{db_password}</td>
              </tr>
              {extra_rows}
            </table>

            <!-- Warning box -->
            <div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:14px 18px;border-radius:6px;margin:20px 0;">
              <p style="margin:0;color:#92400e;font-size:13px;">
                ⚠️ <strong>Security Notice:</strong> Do not share these credentials.
                Change your admin password after your first login.
              </p>
            </div>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f9fafb;padding:20px 40px;text-align:center;border-top:1px solid #e5e7eb;">
            <p style="margin:0;color:#9ca3af;font-size:12px;">
              Sent by {settings.APP_NAME} &bull; This is an automated message.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def send_store_credentials_email(
    recipient_email: str,
    store_name: str,
    store_type: str,
    store_url: str,
    admin_url: str,
    admin_user: str,
    admin_password: str,
    db_password: str,
    extra: dict | None = None,
) -> bool:
    """
    Send an email with the store credentials to the user's Google account.

    Uses Gmail SMTP with an App Password (not the user's real password).
    Set SMTP_USERNAME and SMTP_APP_PASSWORD in your .env file.

    Returns True on success, False on failure.
    """
    if not settings.SMTP_USERNAME or not settings.SMTP_APP_PASSWORD:
        logger.warning(
            "SMTP credentials not configured (SMTP_USERNAME / SMTP_APP_PASSWORD). "
            "Skipping credential email for store '%s'.",
            store_name,
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎉 Your Store \"{store_name}\" Credentials"
    msg["From"] = f"{settings.APP_NAME} <{settings.SMTP_USERNAME}>"
    msg["To"] = recipient_email

    # Plain-text fallback
    plain = (
        f"Your {store_type} store \"{store_name}\" is ready!\n\n"
        f"Store URL: {store_url}\n"
        f"Admin URL: {admin_url}\n"
        f"Admin User: {admin_user}\n"
        f"Admin Password: {admin_password}\n"
        f"DB Password: {db_password}\n"
    )
    if extra:
        for k, v in extra.items():
            plain += f"{k.replace('_', ' ').title()}: {v}\n"
    plain += "\n⚠️ Keep these credentials safe. Change your password after first login."

    html = _build_html_body(
        store_name=store_name,
        store_type=store_type,
        store_url=store_url,
        admin_url=admin_url,
        admin_user=admin_user,
        admin_password=admin_password,
        db_password=db_password,
        extra=extra,
    )

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USERNAME, settings.SMTP_APP_PASSWORD)
            server.sendmail(settings.SMTP_USERNAME, recipient_email, msg.as_string())
        logger.info(
            "Credential email sent to %s for store '%s'", recipient_email, store_name
        )
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(
            "SMTP authentication failed – verify SMTP_APP_PASSWORD is a valid "
            "Google App Password (not your account password). Error: %s",
            e,
        )
        return False
    except Exception as e:
        logger.exception("Failed to send credential email to %s: %s", recipient_email, e)
        return False
