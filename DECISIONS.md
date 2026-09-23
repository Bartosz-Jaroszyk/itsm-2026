---
svcdesk_decisions:
  C1: wallclock
  C2: immutable
  C3: vip
---
<!-- ai-generated: 90% - drafted with AI from the published requirements and reviewed against the running service decisions -->

# Decisions

## C1 - SLA clock for P1

**Decision:** P1 acknowledgement and resolution targets use wall-clock time, including nights and weekends.

**Rejected alternative:** We rejected business-hours timing for P1 because a critical outage cannot wait until the next office opening.

**Reason:** P1 means the organisation is severely disrupted, so measuring continuously provides an unambiguous emergency commitment and encourages immediate response.

**Service owner:** The IT Service Desk Manager owns this decision because the role is accountable for critical-incident targets, staffing coverage, and escalation performance.

**Customer outcome:** Reporters receive a predictable emergency deadline at any time of day. A Friday-evening P1 is visibly late after its target rather than being hidden until Monday.

## C2 - Closed tickets and reopening

**Decision:** Closed tickets are immutable; only resolved tickets may be reopened within seven days of resolution.

**Rejected alternative:** We rejected reopening closed tickets because changing a confirmed record would weaken audit history and make closure reporting unreliable.

**Reason:** Closure represents confirmed completion and should remain an auditable fact. A failed fix after closure must be reported as a new related ticket.

**Service owner:** The ITSM Process Owner owns this decision because the role governs lifecycle controls, auditability, and the distinction between completed work and follow-up work.

**Customer outcome:** Customers retain a trustworthy history of what was closed and when. If an issue returns, a related new ticket preserves continuity without rewriting the original record.

## C3 - VIP reporters and the priority matrix

**Decision:** A VIP reporter raises any matrix result of P3 or P4 to P2; P1 and P2 priorities remain unchanged.

**Rejected alternative:** We rejected applying the matrix alone because an executive or other designated VIP issue could otherwise wait behind lower-risk work despite its organisational visibility.

**Reason:** The upgrade provides a bounded service response for strategically important reporters without allowing VIP status to turn every issue into an emergency P1.

**Service owner:** The IT Service Desk Manager owns this decision because the role approves priority policy, protects fairness in queue management, and reviews VIP classifications.

**Customer outcome:** VIP reporters receive faster attention for lower-impact requests while genuine P1 incidents retain the highest priority. The rule remains transparent and consistent for agents.
