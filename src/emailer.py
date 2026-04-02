"""Gmail SMTP email sender."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def build_subject(report_time: str, total_articles: int) -> str:
    """Build email subject like: 📊 AI动态日报 · 4月1日 晚间版 · 47条动态"""
    parts = report_time.split(" ")
    date_part = parts[0]
    time_part = parts[1] if len(parts) > 1 else "10:00"

    month = int(date_part.split("-")[1])
    day = int(date_part.split("-")[2])
    hour = int(time_part.split(":")[0])

    period = "上午版" if hour < 14 else "晚间版"
    return f"📊 AI动态日报 · {month}月{day}日 {period} · {total_articles}条动态"


def send_email(
    html_body: str,
    subject: str,
    from_addr: str,
    to_addrs: list[str],
    smtp_host: str,
    smtp_port: int,
    password: str,
) -> None:
    """Send HTML email via SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)

    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(html_part)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addrs, msg.as_string())
