"""Resumen diario por email (Fase C): misma lógica de selección que la app."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User
from app.core.timezones import resolve_effective_timezone
from app.services.mail import smtp_configured, send_email, build_tip_digest_bodies
from app.services.plan_policy import apply_plan_policy
from app.services.selector import pick_daily_bundle


def send_daily_email_digests(db: Session, target_date: date) -> int:
    """
    Envía un correo por usuario activo con email_digest_enabled.
    No crea filas Delivery (evita duplicar con canal app); es aviso/digest.
    Devuelve cuántos correos se enviaron.
    """
    if not smtp_configured():
        return 0

    users = list(
        db.scalars(
            select(User).where(
                User.is_active.is_(True),
                User.email_digest_enabled.is_(True),
            )
        ).all()
    )
    sent = 0
    date_label = target_date.isoformat()

    for user in users:
        try:
            tz = resolve_effective_timezone(None, user.iana_timezone)
            topics_allowed, per_topic_eff = apply_plan_policy(db, user, 1)
            bundle = pick_daily_bundle(
                db=db,
                user_id=user.id,
                per_topic=per_topic_eff,
                strategy="latest",
                tz_name=tz,
                topics_override=topics_allowed,
            )
            tips_flat = [tip for _, tips_list in bundle for tip in tips_list]

            if not tips_flat:
                continue

            for tip in tips_flat:
                _ = tip.topic

            subject = f"Tips — {date_label} ({len(tips_flat)} tip(s))"
            text_body, html_body = build_tip_digest_bodies(tips_flat, date_label)
            send_email(user.email, subject, text_body, html_body)
            sent += 1
        except Exception as exc:
            print(f"[EMAIL] No se pudo enviar a {user.email!r}: {exc!r}")

    return sent


def run_email_digest(db: Session, target_date: date | None = None) -> int:
    if target_date is None:
        target_date = date.today()
    if not smtp_configured():
        print("[EMAIL] SMTP no configurado (SMTP_HOST); se omite el digest.")
        return 0
    n = send_daily_email_digests(db, target_date)
    print(f"[EMAIL] Digest enviado a {n} usuario(s).")
    return n
