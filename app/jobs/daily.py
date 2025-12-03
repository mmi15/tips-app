# app/jobs/daily.py
from __future__ import annotations

from datetime import date
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.ingest import ingest_all_configured_feeds
from app.services.selector import create_daily_deliveries_for_all_users


def run_daily_job(target_date: date | None = None) -> None:
    if target_date is None:
        target_date = date.today()

    db: Session = SessionLocal()
    try:
        print(
            f"[DAILY] Ejecutando job diario para fecha={target_date.isoformat()}")

        new_tips = ingest_all_configured_feeds(db)
        print(f"[DAILY] Ingesta completada. Nuevos tips: {new_tips}")

        deliveries_count = create_daily_deliveries_for_all_users(
            db, target_date=target_date)
        print(
            f"[DAILY] Deliveries creados para {target_date}: {deliveries_count}")

        print("[DAILY] Job diario completado OK.")
    except Exception as e:
        print(f"[DAILY] ERROR en job diario: {e!r}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Permite ejecutar el job a mano:
    #   python -m app.jobs.daily
    run_daily_job()
