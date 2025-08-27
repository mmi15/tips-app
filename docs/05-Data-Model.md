# Data Model

## Entities

**User**

- id, email\* (unique), password_hash, plan, created_at

**Topic**

- id, slug\* (unique), name, description, is_active

**Subscription**

- id, user_id, topic_id, created_at, is_active
- UNIQUE(user_id, topic_id)

**Tip**

- id, topic_id, title, body, source_url?, source_name?, lang, fingerprint\* (unique), quality_score, created_at

**Delivery**

- id, user_id, topic_id, tip_id, delivered_at, channel, status

## Rules

- Fingerprint must be unique (combination of title + body + url).
- A tip cannot be delivered twice to the same user.
- Deliveries keep the complete history of sent tips.
