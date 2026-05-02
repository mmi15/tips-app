"""Tests del digest por email (sin SMTP real)."""

from datetime import date
from unittest.mock import patch

from app.db.session import SessionLocal
from app.services.email_digest import send_daily_email_digests, run_email_digest


def test_send_digest_skips_without_smtp():
    db = SessionLocal()
    try:
        with patch("app.services.email_digest.smtp_configured", return_value=False):
            n = send_daily_email_digests(db, date.today())
        assert n == 0
    finally:
        db.close()


def test_run_email_digest_prints_when_no_smtp(capsys):
    db = SessionLocal()
    try:
        with patch("app.services.email_digest.smtp_configured", return_value=False):
            n = run_email_digest(db, target_date=date.today())
        assert n == 0
        out = capsys.readouterr().out
        assert "SMTP" in out or "omit" in out.lower()
    finally:
        db.close()
