# Quality Scoring

## Dimensions (0–100)

- **Clarity:** Is the text easy to understand?
- **Usefulness:** Is there actionable or valuable advice?
- **Novelty:** Is the tip not too similar to recent tips in the same topic?
- **Safety:** Avoid harmful or misleading recommendations.

## Quick Rules (MVP)

- If length > 400 characters → -15 points.
- If the text contains miracle claims ("cure", "guaranteed") → -20 points.
- If similarity > 0.9 with another tip in the same topic → discard.

## Publishing Threshold

- Only publish tips with a score ≥ 60.
- Tips below this threshold are kept but not delivered until reviewed.
