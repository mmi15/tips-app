# Runbook

## Local Development

- Start API: `uvicorn app.main:app --reload`
- Run ingestion manually: `python worker/schedule.py`
- Load test data: seed topics and a demo user.

## Health Checks

- Check ingestion logs for errors or failed sources.
- Verify at least one new tip per active topic daily.

## Common Incidents

- **429 or timeout from AI API:** retry with exponential backoff.
- **Broken feeds:** disable or replace the source.
- **Duplicate tips:** check fingerprint logic.

## Maintenance

- Rotate API keys regularly.
- Backup database weekly.
