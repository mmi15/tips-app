# Ingestion Pipeline

## Sources

- 3–5 RSS feeds per topic.
- Fallback: HTML parsing when feed summaries are missing.

## Steps

1. Parse feed entries (title, link, summary).
2. If summary is missing, fetch HTML and extract first paragraph.
3. Send content to AI with the reformulation prompt.
4. Generate fingerprint and check for duplicates.
5. Save tip with initial quality_score.

## Frequency

- Run ingestion 2–4 times per day per topic.

## Error Handling

- Use retry with exponential backoff on network or AI errors.
- Log failed URLs and skip if consistently failing.

## Output

- Clean, deduplicated, AI-reformulated tips stored in the database.
