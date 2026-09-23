# ai-generated: 85% - created for the Lab 1 Stretch S3 conformance runner
"""Small dependency-free integration suite for the running svcdesk service."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any


BASE_URL = os.environ.get("SVCDESK_URL")
if not BASE_URL:
    raise SystemExit("SVCDESK_URL is required")
BASE_URL = BASE_URL.rstrip("/")
TEST_CLOCK = "2026-10-14T10:00:00Z"


def request(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    expected_status: int = 200,
) -> dict[str, Any] | list[dict[str, Any]]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json", "X-Test-Clock": TEST_CLOCK}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"{BASE_URL}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            payload = json.loads(response.read())
    except urllib.error.HTTPError as response:
        status = response.code
        payload = json.loads(response.read())
    if status != expected_status:
        raise AssertionError(f"{method} {path}: expected {expected_status}, got {status}")
    return payload


def create(
    title: str = "Stretch S3 ticket",
    impact: int = 2,
    urgency: int = 2,
    vip: bool = False,
) -> dict[str, Any]:
    return request(
        "POST",
        "/tickets",
        {
            "title": title,
            "description": "Integration test ticket",
            "reporter": {"name": "S3 Runner", "vip": vip},
            "impact": impact,
            "urgency": urgency,
        },
        201,
    )


def test_health() -> None:
    assert request("GET", "/health") == {"status": "ok", "service": "svcdesk"}


def test_create_defaults() -> None:
    ticket = create()
    assert ticket["state"] == "new" and ticket["priority"] == "P3"
    assert ticket["description"] == "Integration test ticket"


def test_get_ticket() -> None:
    ticket = create("Get ticket")
    fetched = request("GET", f"/tickets/{ticket['id']}")
    assert fetched["id"] == ticket["id"] and fetched["title"] == "Get ticket"


def test_priority_matrix() -> None:
    assert create("Matrix P1", 1, 1)["priority"] == "P1"
    assert create("Matrix P4", 3, 3)["priority"] == "P4"


def test_vip_priority() -> None:
    assert create("VIP escalation", 3, 3, True)["priority"] == "P2"


def test_list_and_filter() -> None:
    ticket = create("Filtered ticket", 1, 2)
    listed = request("GET", "/tickets?priority=P2")
    assert any(item["id"] == ticket["id"] for item in listed)


def test_lifecycle() -> None:
    ticket = create("Lifecycle ticket")
    ticket = request("POST", f"/tickets/{ticket['id']}/ack")
    ticket = request("POST", f"/tickets/{ticket['id']}/start")
    ticket = request("POST", f"/tickets/{ticket['id']}/resolve")
    ticket = request("POST", f"/tickets/{ticket['id']}/close")
    assert ticket["state"] == "closed" and ticket["closed_at"] is not None


def test_invalid_transition() -> None:
    ticket = create("Invalid transition")
    error = request("POST", f"/tickets/{ticket['id']}/resolve", expected_status=409)
    assert "error" in error


def test_sla_details() -> None:
    ticket = create("SLA ticket", 2, 2)
    details = request("GET", f"/tickets/{ticket['id']}/sla")
    assert details["priority"] == "P3"
    assert details["ack_due_at"] and details["resolve_due_at"]
    assert details["ack_breached"] is False


def test_validation_error() -> None:
    error = request(
        "POST",
        "/tickets",
        {"title": "", "reporter": {"name": ""}, "impact": 9, "urgency": 1},
        expected_status=422,
    )
    assert "error" in error


def main() -> int:
    deadline = time.monotonic() + 30
    while True:
        try:
            test_health()
            break
        except Exception:
            if time.monotonic() >= deadline:
                print("ITSMLAB-TESTS: passed=0 failed=10")
                return 1
            time.sleep(1)

    tests = [
        test_health,
        test_create_defaults,
        test_get_ticket,
        test_priority_matrix,
        test_vip_priority,
        test_list_and_filter,
        test_lifecycle,
        test_invalid_transition,
        test_sla_details,
        test_validation_error,
    ]
    passed = 0
    failures: list[str] = []
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as exc:
            failures.append(f"{test.__name__}: {exc}")
    for failure in failures:
        print(f"FAIL: {failure}")
    failed = len(tests) - passed
    print(f"ITSMLAB-TESTS: passed={passed} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
