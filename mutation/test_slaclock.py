# ai-generated: 100% - behavioral mutation tests for Lab 5 Stretch 1
from datetime import datetime

import pytest

import slaclock


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [
        (1, 1, "P1"),
        (1, 2, "P2"),
        (2, 1, "P2"),
        (2, 2, "P3"),
        (3, 2, "P4"),
    ],
)
def test_priority_matrix(impact: int, urgency: int, expected: str) -> None:
    assert slaclock.priority_of(impact, urgency) == expected


def test_vip_priority_floor() -> None:
    assert slaclock.priority_of(3, 3, vip=True) == "P2"
    assert slaclock.priority_of(1, 1, vip=True) == "P1"


def test_priority_inputs_must_be_integers_one_through_three() -> None:
    for impact, urgency in [(0, 1), (4, 1), (2.0, 1), (True, 1), ("1", 1)]:
        with pytest.raises(ValueError):
            slaclock.priority_of(impact, urgency)


def test_targets_for_each_priority() -> None:
    assert slaclock.targets("P1") == (15, 240)
    assert slaclock.targets("P2") == (60, 480)
    assert slaclock.targets("P3") == (240, 1440)
    assert slaclock.targets("P4") == (480, 4320)


def test_targets_reject_unknown_priority() -> None:
    with pytest.raises(ValueError):
        slaclock.targets("p1")


def test_sla_state_boundaries() -> None:
    assert slaclock.sla_state(74, 100) == "ok"
    assert slaclock.sla_state(75, 100) == "warning"
    assert slaclock.sla_state(100, 100) == "warning"
    assert slaclock.sla_state(101, 100) == "breached"


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 1, 5, 7, 59), False),
        (datetime(2026, 1, 5, 8, 0), True),
        (datetime(2026, 1, 5, 15, 59), True),
        (datetime(2026, 1, 5, 16, 0), False),
        (datetime(2026, 1, 10, 12, 0), False),
    ],
)
def test_business_time_window(moment: datetime, expected: bool) -> None:
    assert slaclock.is_business_time(moment) is expected


def test_business_minutes_can_end_exactly_at_closing() -> None:
    assert slaclock.add_business_minutes(datetime(2026, 1, 5, 15, 30), 30) == datetime(
        2026, 1, 5, 16, 0
    )


def test_zero_business_minutes_preserve_or_advance_start() -> None:
    assert slaclock.add_business_minutes(datetime(2026, 1, 5, 8, 0), 0) == datetime(
        2026, 1, 5, 8, 0
    )
    assert slaclock.add_business_minutes(datetime(2026, 1, 5, 16, 0), 0) == datetime(
        2026, 1, 6, 8, 0
    )


def test_business_minutes_skip_weekends() -> None:
    assert slaclock.add_business_minutes(datetime(2026, 1, 10, 12, 0), 1) == datetime(
        2026, 1, 12, 8, 1
    )
    assert slaclock.business_minutes_between(
        datetime(2026, 1, 9, 15, 0), datetime(2026, 1, 12, 9, 0)
    ) == 120


def test_business_minutes_cross_closing_and_weekend() -> None:
    assert slaclock.add_business_minutes(datetime(2026, 1, 9, 15, 30), 60) == datetime(
        2026, 1, 12, 8, 30
    )
    start = datetime(2026, 1, 5, 8, 30)
    due = slaclock.add_business_minutes(start, 500)
    assert slaclock.business_minutes_between(start, due) == 500


def test_business_minutes_between_rejects_reversed_range() -> None:
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(
            datetime(2026, 1, 5, 9, 0), datetime(2026, 1, 5, 8, 0)
        )


def test_escalation_boundaries() -> None:
    assert slaclock.escalation_tier("P2", breached=False, reopens=0) == 1
    assert slaclock.escalation_tier("P3", breached=False, reopens=1) == 0
    assert slaclock.escalation_tier("P3", breached=False, reopens=2) == 1
    assert slaclock.escalation_tier("P1", breached=True, reopens=2) == 3


def test_duration_parsing_and_minute_boundaries() -> None:
    assert slaclock.parse_duration(" 1h30m ") == 90
    assert slaclock.parse_duration("1d4h5m") == 1685
    assert slaclock.parse_duration("60m") == 60
    assert slaclock.parse_duration("0h60m") == 60
    with pytest.raises(ValueError):
        slaclock.parse_duration("1h60m")
    with pytest.raises(ValueError):
        slaclock.parse_duration("0m")
