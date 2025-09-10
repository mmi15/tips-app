from app.api.routes import users, topics, subscriptions, tips, auth, me
from fastapi import FastAPI
import os
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import User

app = FastAPI(title="Tips API", version="0.6.0")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")


@app.on_event("startup")
def bootstrap_admin():
    if not ADMIN_EMAIL:
        return
    db: Session = SessionLocal()
    try:
        u = db.execute(select(User).where(
            User.email == ADMIN_EMAIL)).scalar_one_or_none()
        if u and not u.is_admin:
            u.is_admin = True
            db.add(u)
            db.commit()
            print(f"[BOOTSTRAP] Usuario {ADMIN_EMAIL} promovido a admin.")
    finally:
        db.close()


app.include_router(users.router)
app.include_router(topics.router)
app.include_router(subscriptions.router)
app.include_router(tips.router)
app.include_router(auth.router)
app.include_router(me.router)
