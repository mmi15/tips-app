"""Tests for /me/preferences and timezone resolution on /me/tips/today."""


def test_preferences_get_default(client, user_headers):
    r = client.get("/me/preferences", headers=user_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["locale"] == "es"
    assert data["iana_timezone"] is None
    assert data["email_digest_enabled"] is False


def test_preferences_patch_and_get(client, user_headers):
    r = client.patch(
        "/me/preferences",
        headers=user_headers,
        json={"locale": "en", "iana_timezone": "America/Lima"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["locale"] == "en"
    assert r.json()["iana_timezone"] == "America/Lima"

    r2 = client.get("/me/preferences", headers=user_headers)
    assert r2.status_code == 200
    assert r2.json()["locale"] == "en"
    assert r2.json()["iana_timezone"] == "America/Lima"


def test_preferences_patch_invalid_timezone(client, user_headers):
    r = client.patch(
        "/me/preferences",
        headers=user_headers,
        json={"iana_timezone": "Not/AZone"},
    )
    assert r.status_code == 422


def test_today_invalid_query_timezone(client, user_headers):
    r = client.get("/me/tips/today?tz=Not/AZone", headers=user_headers)
    assert r.status_code == 422


def test_today_omitted_tz_uses_default_europe_madrid(client, user_headers):
    """No query param and no stored tz → API default (Europe/Madrid)."""
    r = client.get("/me/tips/today?per_topic=1", headers=user_headers)
    assert r.status_code == 200, r.text
    assert "date" in r.json()


def test_today_omitted_tz_uses_stored_timezone(client, user_headers):
    client.patch(
        "/me/preferences",
        headers=user_headers,
        json={"iana_timezone": "Pacific/Kiritimati"},
    )
    r = client.get("/me/tips/today?per_topic=1", headers=user_headers)
    assert r.status_code == 200, r.text


def test_preferences_email_digest(client, user_headers):
    r = client.patch(
        "/me/preferences",
        headers=user_headers,
        json={"email_digest_enabled": True},
    )
    assert r.status_code == 200, r.text
    assert r.json()["email_digest_enabled"] is True
    r2 = client.get("/me/preferences", headers=user_headers)
    assert r2.json()["email_digest_enabled"] is True


def test_today_query_tz_overrides_stored(client, user_headers):
    client.patch(
        "/me/preferences",
        headers=user_headers,
        json={"iana_timezone": "Pacific/Kiritimati"},
    )
    r = client.get(
        "/me/tips/today?per_topic=1&tz=Europe/Madrid", headers=user_headers
    )
    assert r.status_code == 200, r.text
