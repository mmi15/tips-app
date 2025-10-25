# app/main.py

from app.api.routes import users, topics, subscriptions, tips, auth, me, admin
from fastapi import FastAPI
import os
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import User

# ==============================
# FastAPI Application Entry Point
# ==============================
# This file defines the main FastAPI application instance,
# registers all route modules, and runs startup logic such as
# promoting the admin user automatically if configured.

# ------------------------------
# Create FastAPI instance
# ------------------------------
app = FastAPI(title="Tips API", version="0.6.0")

# ------------------------------
# Load environment variables
# ------------------------------
# The admin email is used to identify the user that will be
# promoted to administrator when the app starts.
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

# ------------------------------
# Startup event: promote admin user
# ------------------------------


@app.on_event("startup")
def bootstrap_admin():
    # If no admin email is defined, skip the process
    if not ADMIN_EMAIL:
        return

    # Create a new database session
    db: Session = SessionLocal()
    try:
        # Look up the user with the configured admin email
        u = db.execute(select(User).where(
            User.email == ADMIN_EMAIL)).scalar_one_or_none()

        # If user exists and is not already admin, promote them
        if u and not u.is_admin:
            u.is_admin = True
            db.add(u)
            db.commit()
            print(f"[BOOTSTRAP] User {ADMIN_EMAIL} promoted to admin.")
    finally:
        # Always close the session to free resources
        db.close()


# ------------------------------
# Register API routers
# ------------------------------
# Each module below defines an APIRouter() instance with
# related endpoints. They are all mounted on the main app.
app.include_router(users.router)
app.include_router(topics.router)
app.include_router(subscriptions.router)
app.include_router(tips.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(admin.router)
