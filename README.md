# 📌 Tips App

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-d71f00.svg)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Migrations-Alembic-5a4f7c.svg)](https://alembic.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#-license)

A **personalized daily tips** service built with **FastAPI**, **SQLAlchemy**, and **Alembic**.  
Users subscribe to topics (nutrition, football, manga, etc.) and receive **one daily micro-tip per topic**.

**Freemium model**
- **Free:** up to 3 feeds, ads, 1 tip per topic/day  
- **Premium (planned):** more feeds, ad-free, push/email notifications, re-roll tips, sharing

---

## 🚀 Features

- Topics & subscriptions (list, subscribe, unsubscribe)  
- Daily tip selection & delivery
- RSS ingestion worker (`feedparser`)
- Optional AI-assisted tip generation (OpenAI or compatible provider)
- Database migrations with Alembic
- Tests with `pytest`

---

## 🏗️ Tech Stack

- **FastAPI** (HTTP API)  
- **SQLAlchemy** (ORM) + **Alembic** (migrations)  
- **SQLite** (local dev) → **PostgreSQL** (production)  
- **feedparser** (RSS ingestion)  
- **OpenAI** (optional text generation)

---

## 📁 Project Structure

```
tips-app/
  app/
    __init__.py
    main.py
    db/
      models.py
      session.py
    services/
      ingest.py
      selector.py
    api/
      tips.py
      topics.py
      # (users.py, subscriptions.py, etc. as the project grows)
  tests/
    test_*
  .env
  alembic.ini
  requirements.txt
  README.md
```

---

## ⚡ Getting Started

### 1) Clone & create virtualenv
```bash
git clone https://github.com/<your-username>/tips-app.git
cd tips-app
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix/Mac:
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Configure environment
Create a `.env` file in the project root:
```env
# DB: use SQLite in dev; switch to Postgres in prod
DATABASE_URL=sqlite:///./dev.db
# DATABASE_URL=postgresql+psycopg://USER:PASS@HOST:5432/tips

# Optional: AI generation
OPENAI_API_KEY=sk-...

# App config
APP_ENV=development
FREE_PLAN_MAX_FEEDS=3
TIP_MAX_LENGTH=500

# (If/when JWT auth is added)
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
```

### 4) Run migrations
```bash
alembic upgrade head
```

### 5) Start the server
```bash
uvicorn app.main:app --reload
```

Open:
- Swagger UI → `http://127.0.0.1:8000/docs`  
- ReDoc → `http://127.0.0.1:8000/redoc`

---

## 🔌 API (early WIP)

### Topics
- `GET /topics` – list topics  
- `POST /topics` – create topic *(future: protected/admin)*  
- `GET /topics/{slug}` – topic detail  
- `DELETE /topics/{slug}` – delete topic *(future: protected/admin)*  

### Subscriptions
- `POST /subscribe` – subscribe current user to a topic  
- `DELETE /unsubscribe` – unsubscribe from a topic  

### Tips
- `GET /me/tips/today` – fetch today’s tips for the current user  

**Example (cURL)**
```bash
# List topics
curl -s http://127.0.0.1:8000/topics

# Subscribe
curl -s -X POST http://127.0.0.1:8000/subscribe \
  -H "Content-Type: application/json" \
  -d '{"topic_slug":"nutrition"}'

# Get today's tips
curl -s http://127.0.0.1:8000/me/tips/today
```

> Auth & role scopes will be added as the project evolves.

---

## 🧰 Ingestion & Generation

- **Ingestion** (`app/services/ingest.py`): pull & normalize RSS items with `feedparser`  
- **Selector** (`app/services/selector.py`): pick daily tips (deduplication planned)  
- **AI (optional)**: enrich/generate tips via OpenAI

**Planned**
- Fingerprint-based deduplication
- Per-user selection (interests, freshness, diversity)
- Push/email notifications

---

## 🧪 Testing

```bash
pytest
```

Place unit tests under `tests/` (services, selectors) and integration tests for API endpoints (FastAPI `TestClient`).

---

## 🗺️ Roadmap

- [ ] JWT auth & roles (user/admin)  
- [ ] Tip deduplication (hash/similarity)  
- [ ] Notifications: push + email  
- [ ] Premium plan & payments  
- [ ] Admin dashboard (topics, feeds, moderation)  
- [ ] Observability (structured logs, metrics)  

---

## 🤝 Contributing

PRs are welcome. For substantial changes, please open an issue to discuss scope and design.  
Add tests for new behavior where appropriate.

---

## 📜 License

This project is licensed under the **MIT License**. See `LICENSE` for details.

---

## ✨ Author

Built by **Mónica Melendo** — developer & content creator.  
GitHub: [https://github.com/<your-username>](https://github.com/mmi15)

