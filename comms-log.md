---
lab4_comms:
  awareness: 2026-10-12T07:10:07Z
  detection: 2026-10-12T07:09:19Z
  classification: 2026-10-12T07:30:00Z
  nis2:
    early_warning_due: 2026-10-13T07:10:07Z
    early_warning_sent: 2026-10-12T08:00:00Z
    notification_due: 2026-10-15T07:10:07Z
    notification_sent: 2026-10-12T09:00:00Z
    final_report_due: 2026-11-12T09:00:00Z
  ksc:
    early_warning_due: 2026-10-13T07:09:19Z
    early_warning_sent: 2026-10-12T08:00:00Z
    notification_due: 2026-10-15T07:09:19Z
    notification_sent: 2026-10-12T09:00:00Z
    final_report_due: 2026-11-12T09:00:00Z
  dora:
    initial_due: 2026-10-12T11:30:00Z
    initial_sent: 2026-10-12T08:00:00Z
    intermediate_due: 2026-10-15T08:00:00Z
    intermediate_sent: 2026-10-13T09:00:00Z
    final_due: 2026-11-13T09:00:00Z
  log:
    - {at: 2026-10-12T08:00:00Z, to: CSIRT and competent authority, what: Simulated NIS2 and KSC early warning; simulated DORA initial notification}
    - {at: 2026-10-12T09:00:00Z, to: CSIRT and competent authority, what: Simulated NIS2 and KSC incident notification}
    - {at: 2026-10-13T09:00:00Z, to: competent financial supervisor, what: Simulated DORA intermediate report}
---
<!-- ai-generated: 100% - generated from the supplied incident times and computed regulatory reporting deadlines -->

# Communications log: incident regulatory clocks

This Lab 4 exercise assumes the organisation is in scope for NIS2, the Polish KSC reporting process, and DORA, and that the incident meets the applicable reporting thresholds. The notification timestamps below are simulated exercise entries, not claims that reports were actually submitted. All timestamps are UTC.

## Clock start assumptions

- **KSC detection:** 2026-10-12T07:09:19Z, the incident detection time supplied for this exercise.
- **NIS2 awareness:** 2026-10-12T07:10:07Z, when the on-call acknowledged the alert and became aware of the significant incident.
- **DORA classification:** 2026-10-12T07:30:00Z, an explicit exercise assumption for when triage classifies the incident as major. The supplied incident data does not state a separate classification time.

## Computed deadlines

- **NIS2:** Early warning is due 24 hours after awareness, at 2026-10-13T07:10:07Z. The incident notification is due 72 hours after awareness, at 2026-10-15T07:10:07Z. With the simulated notification sent at 2026-10-12T09:00:00Z, the final report is due one calendar month later, at 2026-11-12T09:00:00Z.
- **KSC:** Early warning is due 24 hours after detection, at 2026-10-13T07:09:19Z. The incident notification is due 72 hours after detection, at 2026-10-15T07:09:19Z. With the simulated notification sent at 2026-10-12T09:00:00Z, the final report is due one calendar month later, at 2026-11-12T09:00:00Z.
- **DORA:** The initial report is due at the earlier of four hours after major classification (2026-10-12T11:30:00Z) and 24 hours after awareness (2026-10-13T07:10:07Z), therefore 2026-10-12T11:30:00Z. The intermediate report is due 72 hours after the simulated initial report at 2026-10-12T08:00:00Z, therefore 2026-10-15T08:00:00Z. The final report is due one calendar month after the simulated intermediate report at 2026-10-13T09:00:00Z, therefore 2026-11-13T09:00:00Z.

## Communications record

| When (UTC) | Recipient | Simulated communication | Applicable clock and deadline |
|---|---|---|---|
| 2026-10-12T08:00:00Z | CSIRT and competent authority | NIS2 and KSC early warning; DORA initial notification | NIS2 due 2026-10-13T07:10:07Z; KSC due 2026-10-13T07:09:19Z; DORA due 2026-10-12T11:30:00Z |
| 2026-10-12T09:00:00Z | CSIRT and competent authority | NIS2 and KSC incident notification | NIS2 due 2026-10-15T07:10:07Z; KSC due 2026-10-15T07:09:19Z; final reports due 2026-11-12T09:00:00Z |
| 2026-10-13T09:00:00Z | Competent financial supervisor | DORA intermediate report | Due 2026-10-15T08:00:00Z; final report due 2026-11-13T09:00:00Z |

These reporting times are computed from the stated assumptions and incident timestamps. The awareness and classification instants should be replaced if the incident record establishes different actual decision times; every associated deadline must then be recalculated from its stated clock start.
