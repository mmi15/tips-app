# scripts/seed_user.py
from passlib.hash import bcrypt
from app.db.session import SessionLocal
from app.db.models import User


def main():
    db = SessionLocal()
    try:
        hashed = bcrypt.hash("secret123")
        user = User(email="test@example.com", hashed_password=hashed)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created user id={user.id} email={user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
