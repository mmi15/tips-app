# Security & Privacy

## Personal Data

- User data: email (unique), password hash, plan type.
- No sensitive data collected beyond authentication details.

## Storage

- Environment variables stored in `.env` files, never in code.
- API keys (OpenAI, SendGrid, etc.) must be kept secret.

## Logging

- No plain-text emails or passwords in logs.
- Errors and ingestion logs should redact sensitive data.

## Compliance

- Support account deletion requests ("right to be forgotten").
- Provide minimal privacy policy in the app and repository.
- Passwords must always be stored hashed (bcrypt).
