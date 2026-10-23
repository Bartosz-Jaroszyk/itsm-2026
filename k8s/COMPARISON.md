# Kubernetes analysis and incident evidence comparison

## Current k8sgpt artifact

`k8sgpt-analyze.json` is currently the requested placeholder (`{"results":[]}`), not the output of a cluster scan. No k8sgpt findings are claimed here. Replace it after installing k8sgpt 0.4.39, creating the kind cluster, deploying OpenTelemetry Demo chart 0.42.3, and running the PowerShell analysis command. The resulting scan will describe the live Kubernetes resources and conditions at scan time; it cannot reproduce the historical state of the incident by itself.

## AI RCA findings

The first RCA ledger identifies failed `ProductCatalogService/GetProduct` server spans during the incident window as the strongest evidence-backed lead. It also finds failed checkout `PlaceOrder` spans, consistent with the customer-facing symptom. The payment `Charge` failure hypothesis is unsupported by the saved snapshot, and the broad high-load/resource-bottleneck hypothesis is not measurable as written. The second ledger adds a useful qualification: the checkout counter does not support the transcript's assertion that it was consistently two throughout the full 07:00–07:20Z range. However, `transcript-2.md` is byte-identical to the first transcript and records the same Qwen model, so the second ledger is a second-pass review, not an independently generated investigation.

## Incident ledger findings

The postmortem records onset at 2026-10-12T07:05:45Z, alert detection at 07:09:19Z, acknowledgement at 07:10:07Z, and recovery at 07:12:19Z. Its computed MTTD, MTTA, and MTTR are 214, 48, and 394 seconds. The saved telemetry shows product-catalog errors increasing alongside checkout errors and the seeded-fault signal. The ledger appropriately treats `productCatalogFailure` as an inference because the snapshot does not expose a direct flag transition. Span counters are not unique affected-customer counts, and the artifacts do not establish the exact rollback action.

## Comparative strengths and weaknesses

k8sgpt's strength is live, resource-oriented diagnosis: it can surface Kubernetes object conditions, scheduling problems, configuration mistakes, and events that are not represented in the historical Prometheus snapshot. Its weakness is that it sees the cluster as it exists when the command runs, so findings can change after recovery and do not prove which dependency caused the October incident. It also depends on access to a reachable cluster and should be treated as a diagnostic lead rather than a causal verdict.

The AI RCA ledger is stronger at structuring competing service-level hypotheses against saved span metrics, while the incident ledger is stronger at preserving the incident's timestamps, response intervals, and operational record. Their weaknesses are bounded telemetry and incomplete causal proof; in addition, the two AI transcripts are duplicates rather than independent evidence. These artifacts answer different questions: k8sgpt can describe current Kubernetes health, the RCA ledger evaluates recorded service signals, and the incident ledger documents the response timeline. A real k8sgpt result should be compared with those records without retroactively treating a present-day cluster observation as proof of historical cause.
