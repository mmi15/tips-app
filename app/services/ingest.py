# app/services/ingest.py
from __future__ import annotations

from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select
import feedparser

from app.db.models import Topic, Tip
from app.services.tips import make_fingerprint


# Mapea el slug del topic a una lista de feeds RSS
#  Cambia estas URLs por las que te interesen de verdad
FEEDS_BY_TOPIC_SLUG: Dict[str, List[str]] = {
    "nutricion": [
        # EJEMPLOS, cámbialos a tu gusto
        "https://www.menshealth.com/health/nutrition/rss",
    ],
    "futbol": [
        "https://www.marca.com/rss/futbol/primera-division.xml",
    ],
    "manga": [
        "https://www.animenewsnetwork.com/all/rss.xml?ann-edition=world",
    ],
    # añade más mapeos según tus topics de demo
}


def _find_topic_by_slug(db: Session, slug: str) -> Topic | None:
    return db.execute(
        select(Topic).where(Topic.slug == slug)
    ).scalar_one_or_none()


def ingest_feed_for_topic(db: Session, topic: Topic, feed_url: str) -> int:
    """
    Lee un feed RSS y crea Tips nuevos para un Topic.
    Devuelve cuántos tips se han creado.
    """
    print(f"[INGEST] Topic={topic.slug} URL={feed_url}")
    feed = feedparser.parse(feed_url)

    new_count = 0

    for entry in feed.entries:
        # Título del tip (limitamos longitud por si acaso)
        title = (entry.get("title") or "").strip()
        if not title:
            continue
        title = title[:255]

        # Cuerpo: cogemos summary/description; si no hay, usamos el título
        summary = (
            entry.get("summary")
            or entry.get("description")
            or ""
        ).strip()

        if not summary:
            body = title
        else:
            # recortamos un poco para no romper el esquema (tú tienes 500 chars, si no recuerdo mal)
            body = summary.replace("\n", " ").strip()
        body = body[:500]

        # URL original del artículo
        source_url = entry.get("link")

        # Fingerprint para deduplicar
        fp = make_fingerprint(topic.id, title, body)

        existing = db.execute(
            select(Tip.id).where(Tip.fingerprint == fp)
        ).scalar_one_or_none()
        if existing:
            continue  # ya tenemos este tip

        tip = Tip(
            topic_id=topic.id,
            title=title,
            body=body,
            source_url=source_url,
            fingerprint=fp,
        )
        db.add(tip)
        db.commit()
        db.refresh(tip)
        new_count += 1
        print(f"[INGEST]   + Tip creado: {tip.title}")

    print(f"[INGEST]   Nuevos tips para {topic.slug}: {new_count}")
    return new_count


def ingest_all_configured_feeds(db: Session) -> int:
    """
    Recorre FEEDS_BY_TOPIC_SLUG y ejecuta ingest_feed_for_topic para cada feed.
    Devuelve el total de tips nuevos creados.
    """
    total_new = 0

    for slug, urls in FEEDS_BY_TOPIC_SLUG.items():
        topic = _find_topic_by_slug(db, slug)
        if not topic:
            print(f"[INGEST] Topic con slug='{slug}' no encontrado. Saltando.")
            continue

        for url in urls:
            total_new += ingest_feed_for_topic(db, topic, url)

    print(f"[INGEST] TOTAL tips nuevos: {total_new}")
    return total_new
