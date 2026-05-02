"""Ejecutar solo el envío de digests por email (sin ingest ni batch deliveries)."""

from __future__ import annotations

from datetime import date

from app.db.session import SessionLocal
from app.services.email_digest import run_email_digest


def main() -> None:
    d = date.today()
    db = SessionLocal()
    try:
        run_email_digest(db, target_date=d)
    finally:
        db.close()


if __name__ == "__main__":
    main()
