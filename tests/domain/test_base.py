"""Domain base model tests."""

from __future__ import annotations

import uuid

import pytest
from pydantic import Field, ValidationError

from app.domain.base import DomainEntity, DomainEvent, StrictModel


class SampleModel(StrictModel):
    name: str = Field(..., min_length=1)


class SampleEvent(DomainEvent):
    event_type: str = ""
    value: int


def test_strict_model_strips_strings_and_forbids_extra() -> None:
    """Strict models strip strings and reject unknown fields."""
    model = SampleModel(name="  Pho  ")

    assert model.name == "Pho"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SampleModel(name="Pho", unknown=1)  # type: ignore[call-arg]


def test_strict_model_validates_assignment() -> None:
    """Assignments are validated after construction."""
    model = SampleModel(name="Pho")

    with pytest.raises(ValidationError):
        model.name = "  "


def test_strict_model_supports_camel_aliases() -> None:
    """Camel-case aliases are accepted alongside field names."""

    class AliasModel(StrictModel):
        full_name: str

    assert AliasModel(fullName="Test User").full_name == "Test User"  # type: ignore[call-arg]
    assert AliasModel(full_name="Test User").full_name == "Test User"


def test_domain_entity_defaults_and_touch() -> None:
    """Entities get identity and timestamps, and touch updates updated_at."""
    entity = DomainEntity()
    original_updated_at = entity.updated_at

    assert isinstance(entity.id, uuid.UUID)
    assert entity.created_at <= entity.updated_at

    entity.touch()
    assert entity.updated_at >= original_updated_at


def test_domain_event_defaults_and_event_type() -> None:
    """Events get identity, timestamp, and class-name event type."""
    event = SampleEvent(value=1)

    assert isinstance(event.event_id, uuid.UUID)
    assert event.event_type == "SampleEvent"
    assert event.value == 1
