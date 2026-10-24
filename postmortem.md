---
lab4_postmortem:
  ticket: "1224ad8d-06a8-4ae3-865a-da2015a4ddb5"
  detecting_alert: ShopCheckoutErrors
  onset: 2026-10-12T07:05:45Z
  detection: 2026-10-12T07:09:19Z
  acknowledgement: 2026-10-12T07:10:07Z
  recovery: 2026-10-12T07:12:19Z
  mttd_seconds: 214
  mtta_seconds: 48
  mttr_seconds: 394
  ##identified_flags: [productCatalogFailure]
  identified_flags:
    - productCatalogFailure
    - productCatalogLockContention
    - paymentFailure
  
---
<!-- ai-generated: 25% - assembled from the incident ticket, TSDB snapshot, RCA transcript, Lab 4 template, and verified incident command output -->

# Postmortem: Checkout failures propagated from product catalog

## Date

The incident occurred on 2026-10-12; this postmortem was prepared on 2026-10-23.

## Authors

Prepared by the on-call responder, using the ticket, saved telemetry snapshot, and investigation transcript.

## Status

Complete; follow-up action items are in progress and require owners to track their implementation.

## Summary

An injected fault coincided with product-catalog server errors that propagated into checkout. The incident lasted 394 seconds from onset to recovery; ShopCheckoutErrors detected the checkout symptom after 214 seconds.

## Impact

Checkout's `oteldemo.CheckoutService/PlaceOrder` server-span error counter reached 2 by 07:09Z and stayed at 2 in the available samples through recovery. The product-catalog `oteldemo.ProductCatalogService/GetProduct` server-span error counter rose from 0 at 07:07Z to 38 by 07:11Z and remained at 38 at 07:12Z. These are span-counter observations, not a count of unique customer orders; the snapshot does not establish how many distinct users were affected or provide a defensible total for slow requests. The affected operation and counters were queried with `traces_span_metrics_calls_total{service_name="checkout",span_kind="SPAN_KIND_SERVER",status_code="STATUS_CODE_ERROR"}` and `traces_span_metrics_calls_total{service_name="product-catalog",span_kind="SPAN_KIND_SERVER",status_code="STATUS_CODE_ERROR",span_name="oteldemo.ProductCatalogService/GetProduct"}`. The measured incident interval was 07:05:45Z–07:12:19Z, or 394 seconds.

## Root Causes

The confirmed proximate failure was on product-catalog `GetProduct`: its server error counter increased while the seeded injector reported an active fault. Checkout's `PlaceOrder` server spans also recorded errors, consistent with the product-catalog failure propagating through the order flow. `productCatalogFailure` is the flag identified from that symptom and the OpenTelemetry Demo flag behavior; the snapshot does not expose its evaluated value, so the flag attribution is an evidence-based inference, not a directly observed flag transition.

## Trigger

The seeded fault was reported armed before the onset and active in the subsequent minute samples. The onset recorded by the Lab 4 incident command was 2026-10-12T07:05:45Z. Product-catalog errors appear in the one-minute samples after onset; the evidence supports `productCatalogFailure` as the likely trigger, although the snapshot does not expose its flag-value transition directly.

## Resolution

The incident command records recovery at 2026-10-12T07:12:19Z. The TSDB's `seeded_fault_active` series is 1 in the 07:12Z sample and 0 in the 07:13Z sample, consistent with the fault ending around the reported recovery. The supplied ticket and RCA transcript do not record an operator or switch-off command, so the exact time and method used to disable the inferred `productCatalogFailure` flag cannot be confirmed.

## Detection

The `ShopCheckoutErrors` alert detected the checkout error symptom at 07:09:19Z, 214 seconds after onset. The ticket title independently names the same alert. Without this page, the saved artifacts do not identify a person who would otherwise have noticed the customer-facing checkout errors; the telemetry records the symptom but does not establish a separate human detection path.

## Action Items

| Action Item | Type | Owner | Bug |
|---|---|---|---|
| Add a reviewed alert and regression test for product-catalog `GetProduct` server errors alongside the checkout `PlaceOrder` symptom, and verify both against the incident snapshot. | prevent | Observability owner | ITSM-42 |
| Record the injected fault's exact flag key and rollback sequence in the incident runbook, then require the responder to verify the fault is inactive before declaring recovery. | process | Incident commander | ITSM-43 |

## Lessons Learned

### What went well

The checkout symptom generated a named alert, and the incident command produced a reproducible onset, detection, acknowledgement, and recovery record with internally consistent durations.

### What went wrong

The saved RCA transcript contains speculative hypotheses but no test results for them, and the incident evidence does not preserve which flag was disabled. The alert also arrived 214 seconds after the recorded onset.

### Where we got lucky

The seeded fault ended within the captured telemetry window, leaving enough samples to correlate the active-fault interval with product-catalog and checkout errors instead of leaving recovery unknown.

## Timeline

- **2026-10-12 07:04:00Z:** The one-minute `seeded_fault_armed` sample is 1. This is telemetry sample time, not proof of the precise arm action.
- **2026-10-12 07:05:00Z:** Last pre-onset minute sample available before the recorded onset.
- **2026-10-12 07:05:45Z:** Incident onset, as reported by `itsmlab incident 4`.
- **2026-10-12 07:06:00Z:** The one-minute `seeded_fault_active` sample is 1. This bounds the observed transition to the interval after the previous sample; it does not replace the recorded onset.
- **2026-10-12 07:08:00Z:** The product-catalog `GetProduct` server error counter is 15; it was 0 in the 07:07Z sample.
- **2026-10-12 07:09:19Z:** `ShopCheckoutErrors` detects the incident, 214 seconds after onset.
- **2026-10-12 07:10:07Z:** The ticket records acknowledgement, 48 seconds after detection.
- **2026-10-12 07:11:00Z–07:12:00Z:** The product-catalog server error counter reaches 38 and remains there in the next sample.
- **2026-10-12 07:12:19Z:** Recovery time reported by `itsmlab incident 4`; total time from onset is 394 seconds.
- **2026-10-12 07:13:00Z:** The first subsequent minute sample with `seeded_fault_active` equal to 0.

The saved AI transcript proposes hypotheses H1–H4 but does not timestamp their investigation, record results for their individual queries, or show that any hypothesis was acted upon. They are therefore not presented as timed operator actions or confirmed causes. The exact hypothesis text and corresponding queries are preserved in Supporting information.

## Supporting information

- `incident/ticket.json` supplies the ticket ID, title naming `ShopCheckoutErrors`, creation time, acknowledgement time, priority, and SLA deadlines. It does not contain a resolution timestamp.
- `itsmlab incident 4` returned run `fe6ecd21acce7a08`, detecting alert `ShopCheckoutErrors`, onset `2026-10-12T07:05:45Z`, detection `2026-10-12T07:09:19Z`, acknowledgement `2026-10-12T07:10:07Z`, recovery `2026-10-12T07:12:19Z`, MTTD 214 seconds, MTTA 48 seconds, and MTTR 394 seconds.
- `incident/tsdb-snapshot.tar.gz` was queried for `seeded_fault_armed`, `seeded_fault_active`, and the two `traces_span_metrics_calls_total` selectors described in Impact. The feature-flag telemetry visible for cart reports `cartFailure` and `failedReadinessProbe` with result variant `off`; they are not treated as incident flags. `productCatalogFailure` is inferred from the matching product-catalog server-error symptom, not directly read from a flag-evaluation series.
- In `ai-rca/transcript.md`, H1 proposes `traces_span_metrics_calls_total{service_name="checkout", status_code="STATUS_CODE_ERROR", span_name="oteldemo.CheckoutService/PlaceOrder"}`; H2 proposes `traces_span_metrics_calls_total{service_name="checkout", status_code="STATUS_CODE_ERROR", span_name="oteldemo.ProductCatalogService/GetProduct"}`; H3 proposes `traces_span_metrics_calls_total{service_name="checkout", status_code="STATUS_CODE_ERROR", span_name="oteldemo.PaymentService/Charge"}`; H4 proposes `query_range("traces_span_metrics_calls_total{service_name=\"checkout\", status_code=\"STATUS_CODE_ERROR\"}", "2026-10-12T07:00:00Z", "2026-10-12T07:20:00Z", "60s")`. The transcript records the range query response and suggested hypotheses, but not results from running H1–H3 individually.
- The same-day transcript is an investigation aid, not proof that its untested hypotheses are correct. No dashboard export, notification payload, or recorded rollback command is included in the supplied evidence.

## Problem record

- Incident record: Ticket `1224ad8d-06a8-4ae3-865a-da2015a4ddb5`, a P1 checkout incident detected by `ShopCheckoutErrors`.
- Root cause: An active seeded fault coincided with product-catalog `GetProduct` server errors and propagated checkout `PlaceOrder` errors; the exact injected flag and code-level defect are not identified by the available artifacts.
- Known error: Product-catalog server calls failed during the incident and checkout recorded failed `PlaceOrder` server spans, as shown by the TSDB counters.
- Workaround: The seeded fault was no longer active in the 07:13Z sample after the reported 07:12:19Z recovery; the artifact set does not record a specific flag switch-off or its operator.
