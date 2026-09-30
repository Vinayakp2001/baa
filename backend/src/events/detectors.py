"""Event detectors over resolved source records and field observations."""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.events import BusinessEvent, BusinessStatusHistory
from ..models.provenance import FieldObservation, SourceRecord
from ..normalisation.date import normalise_date

_TYPED_EVENT_TYPES = {
	"FEDERAL_INCORPORATION",
	"PROVINCIAL_REGISTRATION",
	"MUNICIPAL_LICENCE_FIRST_ISSUE",
	"MUNICIPAL_LICENCE_RENEWAL",
	"MUNICIPAL_PERMIT_ISSUED",
	"LICENCE_STATUS_CHANGE",
	"REGISTRY_FILING",
	"NNI_REGISTRATION_RENEWAL",
}
_NAME_FIELDS = {"legal_name", "trade_name"}
_LOCATION_FIELDS = {"address", "city", "province", "postal_code"}


def _event_date(record: SourceRecord) -> date | None:
	"""Get a typed event date from normalized fields or source payload values."""
	normalized = record.normalised_payload or {}
	raw = record.raw_payload or {}
	candidates = (
		normalized.get("incorporation_date"),
		normalized.get("issued_date"),
		raw.get("effective date"),
		raw.get("effective_date"),
		raw.get("incorporation_date"),
		raw.get("issue_date"),
		raw.get("registration_date"),
	)
	for value in candidates:
		if value is None:
			continue
		parsed = normalise_date(str(value))
		if parsed is not None:
			return parsed.date()
	return None


def _record_name(record: SourceRecord) -> str | None:
	"""Return the best source-provided name for an event's display value."""
	normalized = record.normalised_payload or {}
	name = normalized.get("name") or {}
	raw = record.raw_payload or {}
	return (
		name.get("legal_name")
		or name.get("trade_name")
		or raw.get("name of corporation")
		or raw.get("company_name")
		or raw.get("business_name")
		or raw.get("name")
	)


async def _existing_events(
	entity_id: uuid.UUID,
	ingestion_run_id: uuid.UUID,
	db: AsyncSession,
) -> list[BusinessEvent]:
	result = await db.execute(
		select(BusinessEvent).where(
			BusinessEvent.entity_id == entity_id,
			BusinessEvent.ingestion_run_id == ingestion_run_id,
		)
	)
	return list(result.scalars().all())


async def detect_new_business_events(
	entity_id: uuid.UUID,
	ingestion_run_id: uuid.UUID,
	source_id: uuid.UUID,
	db: AsyncSession,
) -> list[BusinessEvent]:
	"""Create discovery and typed source events for records resolved in this run."""
	records_result = await db.execute(
		select(SourceRecord).where(
			SourceRecord.entity_id == entity_id,
			SourceRecord.ingestion_run_id == ingestion_run_id,
		)
	)
	records = records_result.scalars().all()
	existing = await _existing_events(entity_id, ingestion_run_id, db)
	existing_keys = {
		(event.event_type, event.event_date, event.raw_value)
		for event in existing
	}
	created: list[BusinessEvent] = []

	for record in records:
		event_date = _event_date(record)
		display_name = _record_name(record)
		event_types: list[str] = []
		if record.resolution_status == "NEW":
			event_types.append("BUSINESS_DISCOVERED")

		normalized_extra = (record.normalised_payload or {}).get("extra") or {}
		raw_payload = record.raw_payload or {}
		typed_event = normalized_extra.get("event_type") or raw_payload.get("event_type")
		if record.source_grain == "EVENT" and typed_event in _TYPED_EVENT_TYPES:
			event_types.append(typed_event)
		elif typed_event == "MUNICIPAL_LICENCE_FIRST_ISSUE":
			# Saskatoon's validated new-licence feed uses licence grain but carries an
			# explicit first-issue event signal.
			event_types.append(typed_event)

		for event_type in event_types:
			raw_value = display_name
			if raw_value is None and event_type == "MUNICIPAL_PERMIT_ISSUED":
				raw_value = (
					raw_payload.get("NUMERO_PERMIS")
					or raw_payload.get("numero_permis")
					or raw_payload.get("permit_number")
				)
			key = (event_type, event_date, raw_value)
			if key in existing_keys:
				continue
			event = BusinessEvent(
				entity_id=entity_id,
				event_type=event_type,
				event_date=event_date,
				event_source=source_id,
				raw_value=raw_value,
				ingestion_run_id=ingestion_run_id,
			)
			db.add(event)
			created.append(event)
			existing_keys.add(key)

	return created


def _observation_value(observation: FieldObservation) -> str | None:
	return observation.normalised_value or observation.raw_value


async def detect_change_events(
	entity_id: uuid.UUID,
	ingestion_run_id: uuid.UUID,
	source_id: uuid.UUID,
	db: AsyncSession,
) -> list[BusinessEvent]:
	"""Create change events by comparing this run's observations to prior values."""
	current_result = await db.execute(
		select(FieldObservation)
		.where(
			FieldObservation.entity_id == entity_id,
			FieldObservation.ingestion_run_id == ingestion_run_id,
			FieldObservation.is_current.is_(True),
		)
		.order_by(FieldObservation.observed_at, FieldObservation.observation_id)
	)
	current_rows = current_result.scalars().all()
	if not current_rows:
		return []

	current_by_field: dict[str, FieldObservation] = {}
	for observation in current_rows:
		current_by_field[observation.field_name] = observation

	previous_result = await db.execute(
		select(FieldObservation)
		.where(
			FieldObservation.entity_id == entity_id,
			FieldObservation.ingestion_run_id != ingestion_run_id,
			FieldObservation.field_name.in_(list(current_by_field)),
		)
		.order_by(FieldObservation.observed_at.desc(), FieldObservation.observation_id.desc())
	)
	previous_by_field: dict[str, FieldObservation] = {}
	for observation in previous_result.scalars().all():
		previous_by_field.setdefault(observation.field_name, observation)

	changes: dict[str, dict[str, str | None]] = {}
	for field_name, current in current_by_field.items():
		previous = previous_by_field.get(field_name)
		if previous is None:
			continue
		old_value = _observation_value(previous)
		new_value = _observation_value(current)
		if old_value != new_value:
			changes[field_name] = {"previous": old_value, "current": new_value}

	if not changes:
		return []

	existing = await _existing_events(entity_id, ingestion_run_id, db)
	existing_types = {event.event_type for event in existing}
	event_date = max(row.observed_at for row in current_by_field.values()).date()
	created: list[BusinessEvent] = []

	def add_event(
		event_type: str,
		changed_fields: set[str],
	) -> BusinessEvent | None:
		if event_type in existing_types:
			return None
		relevant_changes = {
			field: values for field, values in changes.items() if field in changed_fields
		}
		if not relevant_changes:
			return None
		event = BusinessEvent(
			entity_id=entity_id,
			event_type=event_type,
			event_date=event_date,
			event_source=source_id,
			raw_value=json.dumps(
				{field: values["current"] for field, values in relevant_changes.items()},
				sort_keys=True,
			),
			previous_value=json.dumps(
				{field: values["previous"] for field, values in relevant_changes.items()},
				sort_keys=True,
			),
			ingestion_run_id=ingestion_run_id,
		)
		db.add(event)
		created.append(event)
		existing_types.add(event_type)
		return event

	status_change = changes.get("status")
	if status_change and "STATUS_CHANGED" not in existing_types:
		observation = current_by_field["status"]
		db.add(
			BusinessStatusHistory(
				entity_id=entity_id,
				old_status=status_change["previous"],
				new_status=status_change["current"] or "UNKNOWN",
				changed_at=observation.observed_at,
				source_id=source_id,
				ingestion_run_id=ingestion_run_id,
			)
		)
		add_event("STATUS_CHANGED", {"status"})

	add_event("NAME_CHANGED", _NAME_FIELDS)
	add_event("LOCATION_CHANGED", _LOCATION_FIELDS)
	add_event("BUSINESS_UPDATED", set(changes))
	return created
