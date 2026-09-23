<!-- ai-generated: 85% - written from the published requirements and the implemented svcdesk service -->

# Lab 1 `svcdesk` convergence report

The implemented service converges with the Lab 1 specification by exposing the JSON HTTP interface described by
**R-01**. The FastAPI application provides health, ticket creation, listing, retrieval, lifecycle actions, and SLA
endpoints, while validation errors and unknown resources are returned as JSON error objects. Ticket creation
enforces the required title, reporter, impact, and urgency fields, ignores client-owned fields, and computes
priority from the published matrix. The selected C3 decision is also implemented: a VIP reporter raises a matrix
P3 or P4 ticket to P2, without changing P1 or P2.

The lifecycle implementation satisfies the ordering and conflict behavior in R-07 and R-08. Acknowledgement,
start, resolution, and closure are separate transitions with event timestamps; invalid transitions return a
conflict response. In accordance with the C2 decision, closed tickets are immutable, while resolved tickets can be
reopened only within seven days and return to `in_progress` without receiving a new SLA target.

For **R-15**, the `/tickets/{id}/sla` endpoint reports priority, acknowledgement and resolution due instants,
breach flags, and the current paused state. P1 targets use the selected wall-clock C1 behavior, while P2-P4
targets are calculated using Europe/Warsaw business hours. The test-clock header is honored when enabled, making
deadline, equality, breach, pause, and reopening checks deterministic. Finally, **R-22** is addressed by the
Compose project: service `svcdesk` is built from the repository, listens on container port 8080, enables
`SVCDESK_TEST_CLOCK`, uses no host bind mount, and stores service data in a named volume for restart persistence.
