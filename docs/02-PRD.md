# Product Requirements Document (PRD)

## Problem

People want to stay informed or learn something daily without consuming long articles or infinite feeds.

## Solution

A mobile/web app that delivers one short, well-written tip per topic, every day.

## User Stories (MVP)

- US-01: As a user, I want to register and subscribe to topics.
- US-02: As a user, I want to see "my tips for today" (one per topic).
- US-03: As an editor, I want to ingest sources and generate deduplicated tips.
- US-04: As the system, I want to record which tip was delivered to which user.

## Functional Requirements

- Topic selection (active topics only).
- Deduplication by fingerprint.
- Default language: English/Spanish (configurable later).

## Non-Functional Requirements

- API response P95 < 500ms (excluding AI generation).
- Basic logging for ingestion and deliveries.

## Success Metrics

- Retention D1/D7.
- Daily active users.
- Percentage of users with ≥3 active topics.
