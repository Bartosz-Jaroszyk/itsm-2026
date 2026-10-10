---
lab3_first_draft:
  source: ai                    # ai | instructor  (instructor = the no-AI path: the flawed ladder is your draft)
  tool: "GitHub Copilot Free in VS Code, 10 October 2026"                      # TODO: the assistant and its model, where you used it, the date (required with ai)
  ladder: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2.5, 5, 10]                    # TODO: the assistant's boundaries, in seconds, exactly as it gave them
  verdict: refuted                 # confirmed (it resolves your p99, M-11) | refuted (it does not)
  evidence: {p99_seconds: 0.1568, bucket: [0.1, 0.25], relative_width: 0.957}
lab3_flawed_ladder:
  verdict: refuted              # the only admissible verdict (M-27); the evidence is yours to compute
  evidence: {p99_seconds: 0.1568, bucket: [0.04, 0.5], relative_width: 2.933}
---
<!-- ai-generated: 80% - GitHub Copilot generated the initial draft, manually reviewed and prepared for Lab 3 -->
## Prompt

I need an initial, unmeasured draft for Laboratory 3.

The service endpoint is:

GET /kb/search

Please provide:

1. Histogram bucket boundaries in seconds.
2. Two multi-window multi-burn-rate alert rules.

Return:

- histogram bucket boundaries as a list of seconds
- Prometheus alert rule examples
- reasoning for bucket selection
- reasoning for alert burn rates

This is ONLY an initial draft before measurement.
Do not optimize for any measured latency profile.

## Answer

Initial draft (unmeasured)
Assumptions for these examples: latency SLI is the fraction of GET /kb/search requests completing in 0.5 seconds or less, with a 99% objective over 30 days. These are starting policy choices, not measured performance targets; revisit them after measurement.

Histogram bucket boundaries
Finite boundaries, in seconds:

[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2.5, 5, 10]

Prometheus histograms include the +Inf bucket automatically.

Prometheus alert examples

The bad-request ratio below is the rate of requests taking more than 0.5 seconds, divided by the rate of all requests to /kb/search. The le label is text, as in the repository’s Lab 3 guidance.

groups:
  - name: svcdesk-slo
    rules:
      - alert: KbSearchLatencyFastBurn
        expr: |
          (
            1 -
            sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.5"}[1h]))
            /
            sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="+Inf"}[1h]))
          ) > 14.4 * (1 - 0.99)
          and
          (
            1 -
            sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.5"}[5m]))
            /
            sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="+Inf"}[5m]))
          ) > 14.4 * (1 - 0.99)
        for: 2m
        labels:
          service: svcdesk
          slo: latency
          severity: P1
        annotations:
          summary: "GET /kb/search is rapidly burning its latency error budget"

      - alert: KbSearchLatencySlowBurn
        expr: |
          (
            1 -
            sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.5"}[6h]))
            /
            sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="+Inf"}[6h]))
          ) > 6 * (1 - 0.99)
          and
          (
            1 -
            sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.5"}[30m]))
            /
            sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="+Inf"}[30m]))
          ) > 6 * (1 - 0.99)
        for: 10m
        labels:
          service: svcdesk
          slo: latency
          severity: P2
        annotations:
          summary: "GET /kb/search is steadily burning its latency error budget"

Reasoning
Buckets: The tighter spacing below one second gives more useful detail around interactive request latencies, including the provisional 0.5-second threshold. Wider spacing at higher latencies keeps the ladder manageable while still covering a long tail. The boundaries are deliberately generic; measurement should determine whether to move or add buckets.
Fast-burn alert: A 14.4× burn rate across both 1-hour and 5-minute windows is a rapid, sustained signal suitable for a page (P1). At a 99% objective, it corresponds to a 14.4% bad-request ratio; over one hour, that burn rate would consume about 2% of a 30-day error budget.
Slow-burn alert: A 6× burn rate across both 6-hour and 30-minute windows is a less urgent but sustained signal (P2). It corresponds to a 6% bad-request ratio and would consume about 5% of a 30-day error budget over six hours.
Multi-window condition: Requiring both the long and short windows to breach helps avoid paging or notifying on a brief spike while still detecting ongoing budget consumption.
These use the metric and label conventions described in prometheus/alerts.yml and the draft fields in slo.md.

## Verdict on the draft ladder

The arithmetic: the p99 you measured, the bucket of the draft ladder that holds it, its width relative to the p99,
and what `histogram_quantile` could report from that bucket. Then the verdict in one sentence.

## The draft alert rule

What the assistant's alert rule would have done for your SLO, and what you kept of it in `prometheus/alerts.yml`.

## Verdict on the instructor's flawed ladder

The same arithmetic for `buckets-flawed.example.yml`: where its resolution is spent, and where your p99 is.
