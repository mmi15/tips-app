# scripts/seed_demo.py
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Topic, Tip
from app.services.tips import make_fingerprint


TOPICS_DEMO = [
    {
        "name": "Nutrición",
        "slug": "nutricion",
        "tips": [
            {
                "title": "Bebe agua al levantarte",
                "body": "Empieza el día con 1 vaso de agua. Ayuda a rehidratar el cuerpo y a activar la digestión.",
            },
            {
                "title": "Proteína en cada comida",
                "body": "Incluye una fuente de proteína en cada comida para mantener saciedad y preservar masa muscular.",
            },
            {
                "title": "Fruta entera mejor que zumo",
                "body": "La fruta entera aporta más fibra y saciedad que los zumos, incluso si son naturales.",
            },
        ],
    },
    {
        "name": "Fútbol",
        "slug": "futbol",
        "tips": [
            {
                "title": "Calentamiento corto pero intenso",
                "body": "Dedica 5–10 minutos a un calentamiento dinámico antes de jugar para reducir riesgo de lesión.",
            },
            {
                "title": "Mira el cuerpo, no el balón",
                "body": "Al defender, fíjate en la cadera del rival, no en el balón: así evitas caer en amagos fáciles.",
            },
        ],
    },
    {
        "name": "Manga",
        "slug": "manga",
        "tips": [
            {
                "title": "Empieza por obras cortas",
                "body": "Si estás empezando, prueba mangas de 3–5 tomos para no saturarte con historias eternas.",
            },
            {
                "title": "Sigue a tus autores",
                "body": "Cuando te guste un manga, busca otras obras del mismo autor: suelen compartir tono y temas.",
            },
        ],
    },
    {
        "name": "Productividad",
        "slug": "productividad",
        "tips": [
            {
                "title": "Regla de los 5 minutos",
                "body": "Si una tarea te da pereza, comprométete a hacer solo 5 minutos. Muchas veces seguirás sola.",
            },
            {
                "title": "Una cosa importante al día",
                "body": "Cada mañana elige una única tarea clave. Si la haces, el día ya ha merecido la pena.",
            },
        ],
    },
    {
        "name": "Inglés",
        "slug": "ingles",
        "tips": [
            {
                "title": "Input todos los días",
                "body": "Aunque sea solo 10 minutos, escucha o lee algo en inglés cada día. La constancia manda.",
            },
            {
                "title": "Frases completas, no palabras sueltas",
                "body": "Aprende expresiones en contexto. Recordarás mejor cómo se usan que memorizando listas sueltas.",
            },
        ],
    },
]


def seed_topics_and_tips(db: Session) -> None:
    created_topics = 0
    created_tips = 0

    for topic_cfg in TOPICS_DEMO:
        # 1) Crear topic si no existe
        existing_topic = db.execute(
            select(Topic).where(Topic.slug == topic_cfg["slug"])
        ).scalar_one_or_none()

        if existing_topic:
            topic = existing_topic
        else:
            topic = Topic(
                name=topic_cfg["name"],
                slug=topic_cfg["slug"],
                is_active=True,
            )
            db.add(topic)
            db.commit()
            db.refresh(topic)
            created_topics += 1
            print(f"[SEED] Creado topic: {topic.name} ({topic.slug})")

        # 2) Crear tips si no existen (por fingerprint)
        for tip_cfg in topic_cfg["tips"]:
            fp = make_fingerprint(topic.id, tip_cfg["title"], tip_cfg["body"])
            existing_tip = db.execute(
                select(Tip).where(Tip.fingerprint == fp)
            ).scalar_one_or_none()

            if existing_tip:
                continue

            tip = Tip(
                topic_id=topic.id,
                title=tip_cfg["title"],
                body=tip_cfg["body"],
                source_url=None,
                fingerprint=fp,
            )
            db.add(tip)
            db.commit()
            db.refresh(tip)
            created_tips += 1
            print(f"[SEED]   + Tip creado en '{topic.slug}': {tip.title}")

    print(f"[SEED] Topics nuevos: {created_topics}")
    print(f"[SEED] Tips nuevos:   {created_tips}")


def main():
    db = SessionLocal()
    try:
        seed_topics_and_tips(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
