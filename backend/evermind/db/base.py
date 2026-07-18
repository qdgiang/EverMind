"""Shared declarative base. Owner: A (P0), then each module owns its own tables
(architecture.md: "after 0001, each owner migrates their own tables").
"""
from datetime import datetime

from sqlalchemy import JSON, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    type_annotation_map = {
        # (PR #41, B) architecture.md/G54: "storage stays timezone-aware UTC" for
        # every timestamp — every `Mapped[datetime]` gets TIMESTAMPTZ for free.
        # Postgres otherwise silently strips tzinfo on round-trip, which breaks
        # `now - row.ts` arithmetic the moment `now` is timezone-aware.
        datetime: DateTime(timezone=True),
        # (PR #42, A) bare `Mapped[dict]` / `Mapped[list]` annotations map to JSON
        # columns — keeps every module's models importable without boilerplate.
        dict: JSON,
        list: JSON,
        list[dict]: JSON,
        list[str]: JSON,
    }
