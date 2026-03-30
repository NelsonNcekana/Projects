# AI Concierge Data Capture - Implementation Handoff

This handoff maps implementation responsibilities to the new prompt/data-capture contract and schema artifacts.

## Source of truth artifacts

- Prompt contract: `chat-agent-datainno-mvp-1.yaml`
  - Data-capture section starts at `data_capture`
  - Includes lifecycle scope, storage model, ingestion rules, quality checks, and behavior
- Machine validation schema: `event-schema.json`
  - JSON Schema Draft 2020-12
  - Enforces base event shape + per-event `event_metadata` requirements with conditional validation

## Teams and responsibilities

## 1) Backend / Integration Team

### Required implementation
- Emit one event record per meaningful guest action.
- Validate every outgoing event payload against `event-schema.json` before write/publish.
- Populate required top-level fields:
  - `event_type`
  - `event_timestamp` (UTC ISO-8601)
  - `channel` (`whatsapp` or `telegram`)
  - `conversation_id`
  - `event_metadata` (JSON object)
- Link identifiers when known:
  - `customer_id`
  - `stay_id` (primary anchor during active stay)
  - `reservation_id` (especially for `booking_completed`)
- Set `source` when available: `guest`, `assistant`, `system`.

### Event triggering
Implement triggers aligned to prompt `data_capture.logging_triggers`:
- `inquiry`
- `booking_started`
- `booking_completed`
- `service_request`
- `room_service`
- `food_order`
- `complaint`
- `recommendation_click`
- `payment_initiated`
- `payment_completed`

### Idempotency and ordering
- Deduplicate by stable keys where possible:
  - `event_type`, `conversation_id`, `message_id`, `event_timestamp`
- Preserve event order within each conversation/session.

## 2) Data Platform / Data Engineering

### Storage model alignment
Ensure relational model is enforced:
- `customers` (PK: `customer_id`)
- `reservations` (PK: `reservation_id`, FK: `customer_id`)
- `stays` (PK: `stay_id`, FK: `customer_id`, `reservation_id`)
- `events` (PK: `event_id`, FK: `stay_id`, `customer_id`)
- `payments` (PK: `payment_id`, FK: `stay_id`)

### Pipeline rules
- Reject events that fail schema validation.
- Reject unknown `event_type` or `channel`.
- Reject non-object `event_metadata`.
- Normalize `event_timestamp` to UTC in ingestion layer.

### Quality checks (must implement)
- `booking_completed` must include `reservation_id`.
- `payment_completed.status` should reconcile with `payments.payment_status`.
- If stay is active, enforce `stay_id` presence on stay-related events.
- Enforce `customer_id` whenever identity is known.

## 3) Analytics / BI Team

### Core marts and KPIs
- Build event funnel by lifecycle:
  - reservation -> check_in -> stay -> activities -> check_out
- KPIs:
  - Inquiry volume and response-time distributions
  - Booking start-to-complete conversion
  - Service request volume by type/priority
  - Complaint rate and severity trend
  - Recommendation engagement (`recommendation_click`)
  - Payment initiated vs completed conversion

### Dimensional modeling guidance
- Grain for fact table: one row per `event_id`.
- Primary joins:
  - `events.customer_id -> customers.customer_id`
  - `events.stay_id -> stays.stay_id`
  - `stays.reservation_id -> reservations.reservation_id`

## 4) QA / Test Engineering

### Contract tests (required)
- Validate accepted payload for each event type.
- Validate rejection cases:
  - missing required top-level fields
  - invalid enum values
  - invalid metadata type
  - missing required metadata for specific `event_type`
- Validate date/time format constraints (`date`, `date-time`).

### Integration tests
- Confirm triggered events fire once per action.
- Confirm duplicate inbound action does not create duplicate event.
- Confirm event ordering preserved within same conversation.

## 5) Product / Operations

### Operational expectations
- Data capture is silent to guests (no raw logging details in responses).
- Agent should log only confirmed/explicit facts (no guessing).
- Escalation events and complaint traces must be available for staff follow-up.

## Event payload quick example

```json
{
  "event_id": "evt_123",
  "event_type": "inquiry",
  "event_timestamp": "2026-03-30T20:15:00Z",
  "channel": "whatsapp",
  "conversation_id": "conv_987",
  "customer_id": "cus_101",
  "stay_id": "stay_555",
  "source": "guest",
  "event_metadata": {
    "question": "What time is breakfast?",
    "response_time_seconds": 4.2
  }
}
```

## Rollout checklist

- [ ] Backend validates payloads against `event-schema.json`
- [ ] Event trigger map implemented for all defined event types
- [ ] Data pipeline rejects invalid events and normalizes timestamps
- [ ] QA suite covers positive + negative schema cases
- [ ] Analytics marts updated for funnel and KPI tracking
- [ ] Monitoring added for ingestion failure rate and event lag

