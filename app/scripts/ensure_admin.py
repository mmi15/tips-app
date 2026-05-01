"""
Promocionar o crear un usuario administrador (sobre todo en local/dev).

Uso (desde la raíz del repo):
  python -m app.scripts.ensure_admin admin@ejemplo.com
      Si el usuario existe, lo marca como admin.

  python -m app.scripts.ensure_admin admin@ejemplo.com --password miSecreta
      Si no existe, lo crea con esa contraseña (mín. 6 caracteres) y admin.
"""
from __future__ import annotations

import argparse
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import User
from app.db.session import SessionLocal


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Crear o promover usuario admin.")
    p.add_argument("email", help="Email del usuario")
    p.add_argument(
        "--password",
        help="Si el usuario no existe, contraseña inicial (mín. 6 caracteres)",
    )
    args = p.parse_args(argv)

    email = args.email.strip()
    if not email:
        print("Indica un email válido.", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user:
            if not user.is_admin:
                user.is_admin = True
                db.add(user)
                db.commit()
                print(f"Usuario existente promovido a admin: {email}")
            else:
                print(f"Ya era admin: {email}")
            return 0

        if not args.password or len(args.password) < 6:
            print(
                "No existe ese usuario. Pasa --password (mín. 6 caracteres) para crearlo.",
                file=sys.stderr,
            )
            return 1

        user = User(
            email=email,
            hashed_password=hash_password(args.password),
            is_admin=True,
        )
        db.add(user)
        db.commit()
        print(f"Usuario admin creado: {email}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
