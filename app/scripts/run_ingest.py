# scripts/run_ingest.py
from app.db.session import SessionLocal
from app.services.ingest import ingest_all_configured_feeds


def main():
    db = SessionLocal()
    try:
        ingest_all_configured_feeds(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
