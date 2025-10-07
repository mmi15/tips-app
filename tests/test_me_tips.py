import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import Tip, Topic, Subscription, Delivery


def _create_topic(client, admin_headers, name="Nutrición", slug="nutricion"):
    res = client.post(
        "/topics", json={"name": name, "slug": slug, "is_active": True}, headers=admin_headers)
    assert res.status_code == 201
    return res.json()


def _create_tip(client, admin_headers, topic_id, title, body):
    res = client.post("/tips", json={"topic_id": topic_id, "title": title,
                      "body": body, "source_url": None}, headers=admin_headers)
    assert res.status_code == 201
    return res.json()


def _subscribe(client, user_headers, topic_id):
    res = client.post("/subscriptions",
                      json={"topic_id": topic_id}, headers=user_headers)
    assert res.status_code in (200, 201)
    return res.json()


@pytest.mark.parametrize("per_topic", [1, 2])
def test_today_registers_deliveries_and_history(client, db_session: Session, admin_headers, user_headers, per_topic):
    # 1) Topic + tips
    topic = _create_topic(client, admin_headers(), name="Manga", slug="manga")
    for i in range(5):
        _create_tip(client, admin_headers(),
                    topic_id=topic["id"], title=f"Tip {i}", body=f"Cuerpo {i}")

    # 2) Suscripción
    _subscribe(client, user_headers(), topic_id=topic["id"])

    # 3) Llamada a today (crea deliveries)
    r = client.get(
        f"/me/tips/today?per_topic={per_topic}", headers=user_headers())
    assert r.status_code == 200
    payload = r.json()
    assert payload["count"] == per_topic

    # 4) Verifica deliveries en DB (unicidad tip_id+user_id)
    deliveries = db_session.execute(select(Delivery)).scalars().all()
    assert len(deliveries) == per_topic

    # 5) Repetir today NO debe crear duplicados por UNIQUE(tip_id,user_id)
    r2 = client.get(
        f"/me/tips/today?per_topic={per_topic}", headers=user_headers())
    assert r2.status_code == 200
    deliveries_after = db_session.execute(select(Delivery)).scalars().all()
    assert len(deliveries_after) == len(deliveries)  # sin nuevos

    # 6) History lista lo creado
    h = client.get("/me/tips/history?page=1&size=50", headers=user_headers())
    assert h.status_code == 200
    hist = h.json()
    assert hist["total"] == len(deliveries_after)
    assert len(hist["items"]) == len(deliveries_after)
    assert hist["items"][0]["tip"]["title"].startswith("Tip")


def test_today_fallback_when_no_undelivered(client, db_session: Session, admin_headers, user_headers):
    # Topic con 1 tip -> primer today crea 1 delivery, el segundo entra en fallback (no crea nuevo delivery)
    topic = _create_topic(client, admin_headers(),
                          name="Fútbol", slug="futbol")
    tip = _create_tip(client, admin_headers(),
                      topic_id=topic["id"], title="Unico tip", body="...")

    _subscribe(client, user_headers(), topic_id=topic["id"])

    r1 = client.get("/me/tips/today?per_topic=1", headers=user_headers())
    assert r1.status_code == 200

    # ya existe un delivery
    c1 = db_session.query(Delivery).count()
    assert c1 == 1

    # segunda llamada: como no quedan "no entregados", devolverá algo por fallback, pero no debe crear otro delivery
    r2 = client.get("/me/tips/today?per_topic=1", headers=user_headers())
    assert r2.status_code == 200

    c2 = db_session.query(Delivery).count()
    assert c2 == c1  # sigue siendo 1


def test_history_filter_by_topic(client, db_session: Session, admin_headers, user_headers):
    # Crear 2 topics y tips en cada uno
    t1 = _create_topic(client, admin_headers(),
                       name="Nutrición", slug="nutricion")
    t2 = _create_topic(client, admin_headers(), name="Fútbol", slug="futbol")

    for i in range(3):
        _create_tip(client, admin_headers(),
                    topic_id=t1["id"], title=f"N{i}", body=f"N{i}")
    for i in range(2):
        _create_tip(client, admin_headers(),
                    topic_id=t2["id"], title=f"F{i}", body=f"F{i}")

    # Suscribirse a ambos
    _subscribe(client, user_headers(), topic_id=t1["id"])
    _subscribe(client, user_headers(), topic_id=t2["id"])

    # Generar entregas (today registra)
    client.get("/me/tips/today?per_topic=1", headers=user_headers())

    # History total
    all_hist = client.get("/me/tips/history?page=1&size=50",
                          headers=user_headers()).json()
    assert all_hist["total"] == 2  # uno por topic

    # Filtro por t1
    h1 = client.get(
        f"/me/tips/history?page=1&size=50&topic_id={t1['id']}", headers=user_headers()).json()
    assert h1["total"] == 1
    assert h1["items"][0]["topic"]["id"] == t1["id"]

    # Filtro por t2
    h2 = client.get(
        f"/me/tips/history?page=1&size=50&topic_id={t2['id']}", headers=user_headers()).json()
    assert h2["total"] == 1
    assert h2["items"][0]["topic"]["id"] == t2["id"]


def test_mark_delivery_read_idempotent(client, db_session: Session, admin_headers, user_headers):
    # 1) Crear topic/tip y suscribirse
    t = _create_topic(client, admin_headers(),
                      name="Nutrición", slug="nutricion2")
    tip = _create_tip(client, admin_headers(),
                      topic_id=t["id"], title="Tip X", body="Body X")
    _subscribe(client, user_headers(), topic_id=t["id"])

    # 2) Generar entrega con today
    r = client.get("/me/tips/today?per_topic=1", headers=user_headers())
    assert r.status_code == 200

    # 3) Obtener history para saber delivery_id
    h = client.get("/me/tips/history?page=1&size=10",
                   headers=user_headers()).json()
    assert h["total"] >= 1
    delivery_id = h["items"][0]["delivery_id"]

    # 4) PATCH read (estado cambia a read)
    p1 = client.patch(f"/me/tips/{delivery_id}/read", headers=user_headers())
    assert p1.status_code == 200
    assert p1.json()["status"] == "read"

    # 5) Idempotente: repetir PATCH mantiene read
    p2 = client.patch(f"/me/tips/{delivery_id}/read", headers=user_headers())
    assert p2.status_code == 200
    assert p2.json()["status"] == "read"
