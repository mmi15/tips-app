# Delivery & Scheduling

## Daily Selection

- For each active subscription, pick the most recent, undelivered tip.
- Ensure one tip per topic per day.

## Delivery Window (MVP)

- In-app only, when the user requests `/me/tips/today`.
- Delivery is registered in the database once retrieved.

## Delivery Record

- Create a Delivery entry with:
  - user_id, topic_id, tip_id
  - delivered_at timestamp
  - channel = "inapp"
  - status = "sent"

## Future Channels

- Push notifications (Firebase/OneSignal).
- Email delivery (SendGrid, Mailgun).
- Scheduled delivery windows by user preference.
