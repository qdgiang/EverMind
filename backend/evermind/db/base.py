"""Shared declarative base. Owner: A (P0), then each module owns its own tables
(architecture.md: "after 0001, each owner migrates their own tables").
"""
from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # Bare `Mapped[dict]` / `Mapped[list]` annotations map to JSON columns —
    # keeps every module's models importable without per-column boilerplate.
    type_annotation_map = {dict: JSON, list: JSON, list[dict]: JSON, list[str]: JSON}
