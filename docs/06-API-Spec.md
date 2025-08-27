# API Specification

## Authentication (MVP)

- Initially: user_id passed as query parameter (later replaced with JWT).

## Endpoints

### Topics

- `GET /topics`  
  Returns the list of active topics.

### Subscriptions

- `POST /subscriptions/{topic_id}`  
  Subscribe to a topic.

- `DELETE /subscriptions/{topic_id}`  
  Unsubscribe from a topic.

### Tips

- `GET /me/tips/today?user_id=ID`  
  Returns 1 tip per active subscription, registers a Delivery.

- `GET /me/deliveries?user_id=ID`  
  Returns delivery history for the user.

## Response Codes

- `200 OK` – success
- `201 Created` – resource created
- `400 Bad Request` – invalid input
- `401 Unauthorized` – invalid auth
- `404 Not Found` – resource does not exist
