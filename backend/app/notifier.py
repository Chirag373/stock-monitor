import os
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SMTP_EMAIL")
SENDER_PASSWORD = os.getenv("SMTP_PASSWORD")
TARGET_EMAIL = os.getenv("TARGET_EMAIL")
CHART_URL = os.getenv("CHART_URL", "#")


def send_alert_email(
    symbol: str,
    price: float,
    dma_period: int,
    dma_value: float,
    condition: str = "crossed below",
) -> bool:
    if not SENDER_EMAIL or not SENDER_PASSWORD or not TARGET_EMAIL:
        logger.error("Email credentials not set.")
        return False

    if price <= 0 or dma_value <= 0:
        logger.warning(f"Invalid data for {symbol}. Skipping email.")
        return False

    alert_time = datetime.utcnow().isoformat(timespec="seconds") + " UTC"
    subject = f"🚨 ALERT: {symbol} {condition} {dma_period} DMA"

    text_body = f"""
    Stock Alert: {symbol}
    ------------------------
    Price has {condition} the {dma_period} DMA.

    Price: ${price:,.2f}
    DMA: ${dma_value:,.2f}
    Time: {alert_time}

View Chart: {CHART_URL}
"""

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #d32f2f;">Stock Alert: {symbol}</h2>
        <p><strong>{symbol}</strong> has {condition} its <strong>{dma_period} DMA</strong>.</p>
        <ul>
          <li><strong>Current Price:</strong> ${price:,.2f}</li>
          <li><strong>DMA Level:</strong> ${dma_value:,.2f}</li>
          <li><strong>Time:</strong> {alert_time}</li>
        </ul>
        <a href="{CHART_URL}" style="background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Chart</a>
      </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SENDER_EMAIL
        msg["To"] = TARGET_EMAIL
        msg["Subject"] = subject

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, TARGET_EMAIL, msg.as_string())

        logger.info(f"✅ Alert email sent for {symbol}")
        return True

    except Exception as e:
        logger.error(f"❌ Email failed for {symbol}: {e}")
        return False
