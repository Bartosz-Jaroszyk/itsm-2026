# ai-generated: 80% - GitHub Copilot generated the initial implementation, manually reviewed and adjusted
import os
import re
from datetime import datetime, time, timedelta, timezone
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Any, Literal, NoReturn
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field


app = FastAPI()
WARSAW = ZoneInfo("Europe/Warsaw")
UTC = timezone.utc

Priority = Literal["P1", "P2", "P3", "P4"]
State = Literal["new", "acknowledged", "in_progress", "resolved", "closed"]

PRIORITY_MATRIX: dict[tuple[int, int], Priority] = {
    (1, 1): "P1", (1, 2): "P2", (1, 3): "P3",
    (2, 1): "P2", (2, 2): "P3", (2, 3): "P4",
    (3, 1): "P3", (3, 2): "P4", (3, 3): "P4",
}
SLA_TARGETS: dict[Priority, tuple[timedelta, timedelta]] = {
    "P1": (timedelta(minutes=15), timedelta(hours=4)),
    "P2": (timedelta(hours=1), timedelta(hours=8)),
    "P3": (timedelta(hours=4), timedelta(hours=24)),
    "P4": (timedelta(hours=8), timedelta(hours=72)),
}


class Reporter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=1, max_length=100)
    email: str | None = None
    vip: bool = False


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    reporter: Reporter
    impact: Literal[1, 2, 3]
    urgency: Literal[1, 2, 3]
    related_to: str | None = None


class SLA(BaseModel):
    ack_due_at: str
    resolve_due_at: str


class Ticket(BaseModel):
    id: str
    title: str
    description: str
    reporter: Reporter
    impact: int
    urgency: int
    priority: Priority
    state: State
    created_at: str
    acknowledged_at: str | None = None
    resolved_at: str | None = None
    closed_at: str | None = None
    related_to: str | None = None
    sla: SLA


class SLADetails(BaseModel):
    priority: Priority
    ack_due_at: str
    resolve_due_at: str
    ack_breached: bool
    resolve_breached: bool
    paused: bool


tickets: dict[str, Ticket] = {}


def error(code: str, message: str, status: int) -> NoReturn:
    raise HTTPException(status_code=status, detail={"code": code, "message": message})


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {
        "code": "http_error", "message": str(exc.detail)
    }
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0]
    location = ".".join(str(part) for part in first.get("loc", []) if part != "body")
    message = f"{location}: {first['msg']}" if location else first["msg"]
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation", "message": message}},
    )


@app.exception_handler(404)
async def not_found_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "not_found", "message": "path not found"}},
    )


def parse_instant(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone offset")
    return parsed.astimezone(UTC)


def instant_text(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def request_now(test_clock: str | None) -> datetime:
    enabled = os.getenv("SVCDESK_TEST_CLOCK", "").lower() in {"1", "true"}
    if enabled and test_clock is not None:
        try:
            return parse_instant(test_clock)
        except (TypeError, ValueError):
            error("validation", "X-Test-Clock must be an RFC 3339 instant", 400)
    return datetime.now(UTC)


def is_business_time(local: datetime) -> bool:
    return local.weekday() < 5 and time(8) <= local.time() < time(16)


def next_opening(local: datetime) -> datetime:
    candidate = local
    if candidate.weekday() >= 5 or candidate.time() >= time(16):
        candidate = (candidate + timedelta(days=1)).replace(
            hour=8, minute=0, second=0, microsecond=0
        )
    elif candidate.time() < time(8):
        candidate = candidate.replace(hour=8, minute=0, second=0, microsecond=0)
    while candidate.weekday() >= 5:
        candidate = (candidate + timedelta(days=1)).replace(
            hour=8, minute=0, second=0, microsecond=0
        )
    return candidate


def add_business_time(created: datetime, target: timedelta) -> datetime:
    local = created.astimezone(WARSAW)
    remaining = target.total_seconds()
    while True:
        local = next_opening(local)
        available = (local.replace(hour=16, minute=0, second=0, microsecond=0) - local).total_seconds()
        if remaining <= available:
            return (local + timedelta(seconds=remaining)).astimezone(UTC)
        remaining -= available
        local = (local + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)


def due_at(created: datetime, target: timedelta, priority: Priority, is_resolution: bool = False) -> datetime:
    wallclock = priority == "P1"
    if wallclock:
        return created + target
    return add_business_time(created, target)


def compute_priority(impact: int, urgency: int, vip: bool) -> Priority:
    priority = PRIORITY_MATRIX[(impact, urgency)]
    if vip and priority in {"P3", "P4"}:
        return "P2"
    return priority


def get_ticket_or_error(ticket_id: str) -> Ticket:
    ticket = tickets.get(ticket_id)
    if ticket is None:
        error("not_found", "ticket not found", 404)
    return ticket


def clock_header(x_test_clock: Annotated[str | None, Header()] = None) -> datetime:
    return request_now(x_test_clock)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "svcdesk"}


@app.post("/tickets", response_model=Ticket, status_code=201)
def create_ticket(
    payload: TicketCreate,
    x_test_clock: Annotated[str | None, Header()] = None,
) -> Ticket:
    created = request_now(x_test_clock)
    priority = compute_priority(payload.impact, payload.urgency, payload.reporter.vip)
    ack_target, resolve_target = SLA_TARGETS[priority]
    ticket = Ticket(
        id=str(uuid4()),
        title=payload.title,
        description=payload.description,
        reporter=payload.reporter,
        impact=payload.impact,
        urgency=payload.urgency,
        priority=priority,
        state="new",
        created_at=instant_text(created),
        related_to=payload.related_to,
        sla=SLA(
            ack_due_at=instant_text(due_at(created, ack_target, priority)),
            resolve_due_at=instant_text(due_at(created, resolve_target, priority, True)),
        ),
    )
    tickets[ticket.id] = ticket
    return ticket


@app.get("/tickets", response_model=list[Ticket])
def list_tickets(
    state: State | None = None,
    priority: Priority | None = None,
) -> list[Ticket]:
    return [t for t in tickets.values() if (state is None or t.state == state) and
            (priority is None or t.priority == priority)]


@app.get("/tickets/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: str) -> Ticket:
    return get_ticket_or_error(ticket_id)


@app.get("/tickets/{ticket_id}/sla", response_model=SLADetails)
def get_sla(ticket_id: str, x_test_clock: Annotated[str | None, Header()] = None) -> SLADetails:
    ticket = get_ticket_or_error(ticket_id)
    now = request_now(x_test_clock)
    ack_due = parse_instant(ticket.sla.ack_due_at)
    resolve_due = parse_instant(ticket.sla.resolve_due_at)
    acknowledged = parse_instant(ticket.acknowledged_at) if ticket.acknowledged_at else None
    resolved = parse_instant(ticket.resolved_at) if ticket.resolved_at else None
    ack_breached = acknowledged > ack_due if acknowledged else now > ack_due
    resolve_breached = resolved > resolve_due if resolved else now > resolve_due
    resolution_business = ticket.priority != "P1"
    paused = ticket.state not in {"resolved", "closed"} and resolution_business and not is_business_time(now.astimezone(WARSAW))
    return SLADetails(
        priority=ticket.priority,
        ack_due_at=ticket.sla.ack_due_at,
        resolve_due_at=ticket.sla.resolve_due_at,
        ack_breached=ack_breached,
        resolve_breached=resolve_breached,
        paused=paused,
    )


def transition(ticket: Ticket, action: str, now: datetime) -> Ticket:
    expected: dict[str, tuple[State, State]] = {
        "ack": ("new", "acknowledged"),
        "start": ("acknowledged", "in_progress"),
        "resolve": ("in_progress", "resolved"),
        "close": ("resolved", "closed"),
    }
    source, destination = expected[action]
    if ticket.state != source:
        error("invalid_transition", f"cannot {action} ticket from {ticket.state}", 409)
    values = {"state": destination}
    if action == "ack":
        values["acknowledged_at"] = instant_text(now)
    elif action == "resolve":
        values["resolved_at"] = instant_text(now)
    elif action == "close":
        values["closed_at"] = instant_text(now)
    updated = ticket.model_copy(update=values)
    tickets[ticket.id] = updated
    return updated


@app.post("/tickets/{ticket_id}/reopen", response_model=Ticket)
def reopen_ticket(ticket_id: str, x_test_clock: Annotated[str | None, Header()] = None) -> Ticket:
    ticket = get_ticket_or_error(ticket_id)
    now = request_now(x_test_clock)
    if ticket.state == "closed":
        error("ticket_closed", "closed tickets are immutable", 409)
    if ticket.state != "resolved":
        error("invalid_transition", "only resolved tickets can be reopened", 409)
    resolved_at = parse_instant(ticket.resolved_at or ticket.created_at)
    if now > resolved_at + timedelta(days=7):
        error("reopen_window_expired", "reopen window has expired", 409)
    updated = ticket.model_copy(update={"state": "in_progress", "resolved_at": None, "closed_at": None})
    tickets[ticket.id] = updated
    return updated


@app.post("/tickets/{ticket_id}/ack", response_model=Ticket)
def acknowledge_ticket(
    ticket_id: str,
    x_test_clock: Annotated[str | None, Header()] = None,
) -> Ticket:
    return transition(get_ticket_or_error(ticket_id), "ack", request_now(x_test_clock))


@app.post("/tickets/{ticket_id}/start", response_model=Ticket)
def start_ticket(
    ticket_id: str,
    x_test_clock: Annotated[str | None, Header()] = None,
) -> Ticket:
    return transition(get_ticket_or_error(ticket_id), "start", request_now(x_test_clock))


@app.post("/tickets/{ticket_id}/resolve", response_model=Ticket)
def resolve_ticket(
    ticket_id: str,
    x_test_clock: Annotated[str | None, Header()] = None,
) -> Ticket:
    return transition(get_ticket_or_error(ticket_id), "resolve", request_now(x_test_clock))


@app.post("/tickets/{ticket_id}/close", response_model=Ticket)
def close_ticket(
    ticket_id: str,
    x_test_clock: Annotated[str | None, Header()] = None,
) -> Ticket:
    return transition(get_ticket_or_error(ticket_id), "close", request_now(x_test_clock))


@dataclass(frozen=True)
class DoraCommit:
    event_id: str
    at: datetime
    sha: str
    branch: str
    change_id: str | None
    reverts: str | None


@dataclass(frozen=True)
class DoraDeployment:
    event_id: str
    at: datetime
    deployment_id: str
    environment: str
    outcome: str
    commits: tuple[str, ...]
    unplanned: bool
    caused_by: str | None


@dataclass(frozen=True)
class DoraIncident:
    incident_id: str
    opened_at: datetime
    resolved_at: datetime | None
    deployments: tuple[str, ...]


@dataclass(frozen=True)
class DoraIncidentEvent:
    incident_id: str
    at: datetime
    phase: str
    deployments: tuple[str, ...]


DoraEvent = DoraCommit | DoraDeployment | DoraIncidentEvent
RFC3339_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})"
)


def metric_error(message: str) -> NoReturn:
    error("validation", message, 422)


def metric_object(value: Any, description: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        metric_error(f"{description} must be an object")
    return value


def metric_string(
    value: Any,
    description: str,
    *,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        metric_error(f"{description} must be a non-empty string")
    return value


def metric_optional_string(value: Any, description: str) -> str | None:
    if value is None:
        return None
    return metric_string(value, description)


def metric_instant(value: Any, description: str) -> datetime:
    text = metric_string(value, description)
    if not RFC3339_PATTERN.fullmatch(text):
        metric_error(f"{description} must be an RFC 3339 instant with an offset")
    normalized = text.replace("t", "T", 1)
    if normalized.endswith("z"):
        normalized = normalized[:-1] + "Z"
    try:
        return parse_instant(normalized)
    except ValueError:
        metric_error(f"{description} must be an RFC 3339 instant with an offset")


def metric_string_list(value: Any, description: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        metric_error(f"{description} must be an array")
    return tuple(metric_string(item, description) for item in value)


def parse_dora_events(raw_events: list[Any]) -> list[DoraEvent]:
    events: list[DoraEvent] = []
    seen_event_ids: set[str] = set()

    for raw_event in raw_events:
        record = metric_object(raw_event, "each event")
        event_id = metric_string(record.get("event_id"), "event_id")
        if len(event_id) > 64:
            metric_error("event_id must be 1 to 64 characters")
        if event_id in seen_event_ids:
            continue
        seen_event_ids.add(event_id)

        event_type = metric_string(record.get("type"), f"event {event_id} type")
        at = metric_instant(record.get("at"), f"event {event_id} at")
        if event_type == "commit":
            sha = metric_string(record.get("sha"), f"event {event_id} sha")
            branch = metric_string(
                record.get("branch"), f"event {event_id} branch", allow_empty=True
            )
            if "change_id" not in record:
                metric_error(f"event {event_id} is missing change_id")
            change_id = metric_optional_string(
                record["change_id"], f"event {event_id} change_id"
            )
            if "reverts" not in record:
                metric_error(f"event {event_id} is missing reverts")
            reverts = metric_optional_string(
                record.get("reverts"), f"event {event_id} reverts"
            )
            if (reverts is None) != (change_id is not None):
                metric_error(
                    f"event {event_id} must have change_id exactly when reverts is null"
                )
            events.append(DoraCommit(event_id, at, sha, branch, change_id, reverts))
        elif event_type == "deployment":
            deployment_id = metric_string(
                record.get("deployment_id"), f"event {event_id} deployment_id"
            )
            environment = metric_string(
                record.get("environment"),
                f"event {event_id} environment",
                allow_empty=True,
            )
            outcome = metric_string(record.get("outcome"), f"event {event_id} outcome")
            if outcome not in {"success", "failure"}:
                metric_error(f"event {event_id} outcome must be success or failure")
            if type(record.get("unplanned")) is not bool:
                metric_error(f"event {event_id} unplanned must be a boolean")
            if "caused_by" not in record:
                metric_error(f"event {event_id} is missing caused_by")
            caused_by = metric_optional_string(
                record.get("caused_by"), f"event {event_id} caused_by"
            )
            events.append(
                DoraDeployment(
                    event_id,
                    at,
                    deployment_id,
                    environment,
                    outcome,
                    metric_string_list(
                        record.get("commits"), f"event {event_id} commits"
                    ),
                    record["unplanned"],
                    caused_by,
                )
            )
        elif event_type == "incident":
            incident_id = metric_string(
                record.get("incident_id"), f"event {event_id} incident_id"
            )
            phase = metric_string(record.get("phase"), f"event {event_id} phase")
            if phase not in {"opened", "resolved"}:
                metric_error(f"event {event_id} phase must be opened or resolved")
            events.append(
                DoraIncidentEvent(
                    incident_id,
                    at,
                    phase,
                    metric_string_list(
                        record.get("deployments"), f"event {event_id} deployments"
                    ),
                )
            )
        else:
            metric_error(f"event {event_id} has an unsupported type")

    return events


def validate_dora_events(events: list[DoraEvent]) -> tuple[
    dict[str, DoraCommit], dict[str, DoraDeployment], dict[str, DoraIncident]
]:
    commits: dict[str, DoraCommit] = {}
    deployments: dict[str, DoraDeployment] = {}
    incident_phases: dict[str, dict[str, DoraIncidentEvent]] = {}
    incident_deployments: dict[str, set[str]] = {}
    for event in events:
        if isinstance(event, DoraCommit):
            if event.sha in commits:
                metric_error(f"duplicate commit sha: {event.sha}")
            commits[event.sha] = event
        elif isinstance(event, DoraDeployment):
            if event.deployment_id in deployments:
                metric_error(f"duplicate deployment_id: {event.deployment_id}")
            deployments[event.deployment_id] = event
        else:
            phases = incident_phases.setdefault(event.incident_id, {})
            if event.phase in phases:
                metric_error(
                    f"incident {event.incident_id} has multiple {event.phase} events"
                )
            phases[event.phase] = event
            incident_deployments.setdefault(event.incident_id, set()).update(
                event.deployments
            )

    incidents: dict[str, DoraIncident] = {}
    for incident_id, phases in incident_phases.items():
        opened = phases.get("opened")
        resolved = phases.get("resolved")
        if opened is None and resolved is not None:
            metric_error(f"incident {incident_id} resolved without being opened")
        if opened is not None:
            incidents[incident_id] = DoraIncident(
                incident_id,
                opened.at,
                resolved.at if resolved is not None else None,
                tuple(sorted(incident_deployments[incident_id])),
            )

    for commit in commits.values():
        if commit.reverts is not None and commit.reverts not in commits:
            metric_error(f"commit {commit.sha} reverts an unknown sha")
    for deployment in deployments.values():
        if any(sha not in commits for sha in deployment.commits):
            metric_error(f"deployment {deployment.deployment_id} references an unknown sha")
        if deployment.caused_by is not None and deployment.caused_by not in incidents:
            metric_error(
                f"deployment {deployment.deployment_id} references an unknown incident"
            )
    for incident_id, deployment_ids in incident_deployments.items():
        if any(deployment_id not in deployments for deployment_id in deployment_ids):
            metric_error(f"incident {incident_id} references an unknown deployment")

    return commits, deployments, incidents


def duration_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return (
        Decimal(delta.days * 86400 + delta.seconds)
        + Decimal(delta.microseconds) / Decimal(1_000_000)
    )


def rounded_seconds(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def median_seconds(values: list[Decimal]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        median = ordered[middle]
    else:
        median = (ordered[middle - 1] + ordered[middle]) / Decimal(2)
    return rounded_seconds(median)


def rounded_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    rate = (Decimal(numerator) / Decimal(denominator)).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_UP
    )
    return float(rate)


def metric_instant_text(value: datetime) -> str:
    text = value.astimezone(UTC).isoformat(timespec="microseconds")
    prefix, fraction = text.split(".", 1)
    fraction = fraction.removesuffix("+00:00").rstrip("0")
    return f"{prefix}.{fraction}Z" if fraction else f"{prefix}Z"


def dora_metrics(
    window_from: datetime,
    window_to: datetime,
    events: list[DoraEvent],
) -> dict[str, Any]:
    commits, all_deployments, incidents = validate_dora_events(events)
    deployments = [
        deployment
        for deployment in all_deployments.values()
        if deployment.environment == "production"
        and window_from <= deployment.at < window_to
    ]
    successful = [deployment for deployment in deployments if deployment.outcome == "success"]
    failed = [deployment for deployment in deployments if deployment.outcome == "failure"]

    resolved_changes: dict[str, str] = {}

    def change_for(sha: str, visiting: set[str] | None = None) -> str:
        if sha in resolved_changes:
            return resolved_changes[sha]
        commit = commits[sha]
        if commit.reverts is None:
            change_id = commit.change_id
            if change_id is None:
                metric_error(f"commit {sha} is missing its change_id")
        else:
            path = set() if visiting is None else visiting
            if sha in path:
                metric_error("revert chain contains a cycle")
            path.add(sha)
            change_id = change_for(commit.reverts, path)
            path.remove(sha)
        resolved_changes[sha] = change_id
        return change_id

    for sha in commits:
        change_for(sha)

    first_successful_deployment_by_sha: dict[str, datetime] = {}
    for deployment in sorted(successful, key=lambda item: (item.at, item.deployment_id)):
        for sha in deployment.commits:
            current = first_successful_deployment_by_sha.get(sha)
            if current is None or deployment.at < current:
                first_successful_deployment_by_sha[sha] = deployment.at

    lead_times: list[Decimal] = []
    negative_lead_time_pairs = 0
    for sha, deployment_at in first_successful_deployment_by_sha.items():
        lead_time = duration_seconds(deployment_at, commits[sha].at)
        if lead_time < 0:
            negative_lead_time_pairs += 1
            lead_time = Decimal(0)
        lead_times.append(lead_time)

    first_successful_deployment_by_change: dict[str, datetime] = {}
    for sha, deployment_at in first_successful_deployment_by_sha.items():
        change_id = change_for(sha)
        current = first_successful_deployment_by_change.get(change_id)
        if current is None or deployment_at < current:
            first_successful_deployment_by_change[change_id] = deployment_at

    first_commit_by_change: dict[str, datetime] = {}
    for sha, commit in commits.items():
        change_id = change_for(sha)
        current = first_commit_by_change.get(change_id)
        if current is None or commit.at < current:
            first_commit_by_change[change_id] = commit.at

    delivered_change_lead_times: list[Decimal] = []
    for change_id, deployment_at in first_successful_deployment_by_change.items():
        lead_time = duration_seconds(deployment_at, first_commit_by_change[change_id])
        delivered_change_lead_times.append(max(lead_time, Decimal(0)))

    recovery_times: list[Decimal] = []
    open_failures = 0
    recovered_failures = 0
    for deployment in failed:
        covering = [
            incident
            for incident in incidents.values()
            if deployment.deployment_id in incident.deployments
        ]
        covering.sort(key=lambda incident: (incident.opened_at, incident.incident_id.encode("utf-8")))
        recovery = covering[0] if covering else None
        if recovery is None or recovery.resolved_at is None:
            open_failures += 1
            continue
        recovered_failures += 1
        recovery_time = duration_seconds(recovery.resolved_at, deployment.at)
        recovery_times.append(max(recovery_time, Decimal(0)))

    overlapping_incident_pairs = 0
    incident_list = list(incidents.values())
    for index, first in enumerate(incident_list):
        first_end = first.resolved_at or window_to
        for second in incident_list[index + 1 :]:
            second_end = second.resolved_at or window_to
            if first.opened_at < second_end and second.opened_at < first_end:
                overlapping_incident_pairs += 1

    delivered_changes = len(first_successful_deployment_by_change)
    window_days = duration_seconds(window_to, window_from) / Decimal(86400)
    frequency = (
        Decimal(len(deployments)) / window_days
    ).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    rework_deployments = sum(
        deployment.unplanned and deployment.caused_by is not None
        for deployment in deployments
    )

    return {
        "spec_version": "1.0.0",
        "window": {
            "from": metric_instant_text(window_from),
            "to": metric_instant_text(window_to),
        },
        "deployment_frequency_per_day": float(frequency),
        "change_lead_time_seconds_p50": median_seconds(lead_times),
        "failed_deployment_recovery_time_seconds_p50": median_seconds(recovery_times),
        "change_fail_rate": rounded_rate(len(failed), len(deployments)),
        "deployment_rework_rate": rounded_rate(rework_deployments, len(deployments)),
        "counts": {
            "deployments": len(deployments),
            "successful_deployments": len(successful),
            "failed_deployments": len(failed),
            "recovered_failures": recovered_failures,
            "open_failures": open_failures,
            "rework_deployments": rework_deployments,
            "lead_time_pairs": len(lead_times),
            "changes": len(set(resolved_changes.values())),
        },
        "anomalies": {
            "negative_lead_time_pairs": negative_lead_time_pairs,
            "deployments_without_commits": sum(
                not deployment.commits for deployment in deployments
            ),
            "commits_never_on_main": len(
                {
                    sha
                    for deployment in deployments
                    for sha in deployment.commits
                    if commits[sha].branch != "main"
                }
            ),
            "revert_chains_collapsed": sum(
                commit.reverts is not None for commit in commits.values()
            ),
            "overlapping_incident_pairs": overlapping_incident_pairs,
        },
        "ground_truth": {
            "changes_delivered": delivered_changes,
            "true_change_lead_time_seconds_p50": median_seconds(
                delivered_change_lead_times
            ),
        },
    }


@app.post("/dora/metrics")
def calculate_dora_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    window = metric_object(payload.get("window"), "window")
    window_from = metric_instant(window.get("from"), "window.from")
    window_to = metric_instant(window.get("to"), "window.to")
    if window_to <= window_from:
        metric_error("window.to must be after window.from")

    raw_events = payload.get("events")
    if not isinstance(raw_events, list):
        metric_error("events must be an array")
    events = parse_dora_events(raw_events)
    return dora_metrics(window_from, window_to, events)


@app.get("/dora/ticket-events")
def get_ticket_events() -> list[dict[str, str]]:
    phases = (
        ("created", "created_at", "new"),
        ("acknowledged", "acknowledged_at", "acknowledged"),
        ("resolved", "resolved_at", "resolved"),
        ("closed", "closed_at", "closed"),
    )
    stream: list[dict[str, str]] = []
    for ticket in tickets.values():
        for phase, timestamp_field, state in phases:
            timestamp = getattr(ticket, timestamp_field)
            if timestamp is not None:
                stream.append(
                    {
                        "ticket_id": ticket.id,
                        "at": timestamp,
                        "phase": phase,
                        "priority": ticket.priority,
                        "state": state,
                    }
                )
    return sorted(stream, key=lambda event: (event["at"], event["ticket_id"]))
