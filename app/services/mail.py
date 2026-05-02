"""Envío de correo vía SMTP (sin dependencias extra)."""

from __future__ import annotations

import html
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST", "").strip())


def send_email(
    to: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        raise RuntimeError("SMTP_HOST no está configurado")

    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("SMTP_FROM", user or "").strip()
    if not from_addr:
        raise RuntimeError("SMTP_FROM o SMTP_USER debe estar definido")

    use_tls = os.getenv("SMTP_USE_TLS", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    if html_body:
        msg.attach(MIMEText(html_body, "html", "utf-8"))

    timeout = int(os.getenv("SMTP_TIMEOUT_SECONDS", "30"))
    with smtplib.SMTP(host, port, timeout=timeout) as smtp:
        if use_tls:
            smtp.starttls()
        if user:
            smtp.login(user, password)
        smtp.sendmail(from_addr, [to], msg.as_string())


def build_tip_digest_bodies(
    tips: list,
    date_label: str,
) -> tuple[str, str]:
    """Genera texto plano y HTML seguro para un lote de tips ORM."""
    lines_plain: list[str] = [f"Tips — {date_label}", ""]
    blocks_html: list[str] = [f"<p><strong>Tips — {html.escape(date_label)}</strong></p>"]

    for tip in tips:
        title = html.escape(tip.title or "")
        body = html.escape((tip.body or "")[:800])
        topic_name = ""
        if getattr(tip, "topic", None) is not None and tip.topic.name:
            topic_name = html.escape(tip.topic.name)
        lines_plain.append(f"• {tip.title}")
        lines_plain.append(f"  {tip.body[:400]}{'…' if len(tip.body or '') > 400 else ''}")
        lines_plain.append("")
        sub = f" <small>({topic_name})</small>" if topic_name else ""
        blocks_html.append(
            f"<h2 style=\"font-size:1rem;margin:1rem 0 0.25rem;\">{title}{sub}</h2>"
            f"<p style=\"margin:0 0 0.75rem;\">{body.replace(chr(10), '<br/>')}</p>"
        )

    text = "\n".join(lines_plain).strip()
    html_doc = (
        "<!DOCTYPE html><html><body style=\"font-family:system-ui,sans-serif;\">"
        + "".join(blocks_html)
        + "<p style=\"color:#666;font-size:0.85rem;\">Enviado automáticamente.</p>"
        "</body></html>"
    )
    return text, html_doc
