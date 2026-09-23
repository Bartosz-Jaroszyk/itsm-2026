# ai-generated: 80% - GitHub Copilot generated the initial implementation, manually reviewed and adjusted
import os
from datetime import datetime, time, timedelta, timezone
from typing import Annotated, Literal
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


def error(code: str, message: str, status: int) -> None:
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
