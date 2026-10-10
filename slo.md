---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 30d
  slis:
    availability:
      objective: 0.99
      good: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk",http_route="/kb/search",http_response_status_code!~"5.."}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk",http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 432}
    latency:
      objective: 0.99
      threshold_seconds: 0.16
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk",http_route="/kb/search",le="0.16"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk",http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 432}
  alerts:                       # two or more on the SAME sli, with DIFFERENT burn rates (M-16)
    - {alert: KbSearchLatencyFastBurn, sli: latency, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchLatencySlowBurn, sli: latency, burn_rate: 6, long_window: 6h, short_window: 30m}
---
<!-- ai-generated: 80% - AI drafted the SLO rationale from the Lab 3 specification and measured p99 values; reviewed for arithmetic and consistency -->
# SLO for `GET /kb/search`

The SLOs below apply to requests routed to `GET /kb/search`. Both use a rolling 30-day window and are initial
operational objectives based on the measured latency samples, not a claim that one run characterizes every load
condition.

## Availability

The availability SLI counts non-5xx responses as good and all `/kb/search` responses as valid. Its 99% objective
allows at most 1% of requests to fail with a 5xx response. Across a 30-day window, that is an error budget of
0.01, or 432 budget-equivalent minutes (30 x 24 x 60 x 0.01).

The endpoint depends on `kb-index`, so upstream failures that become 502 responses consume this same budget.
Keeping those failures in the SLI reflects the experience of callers rather than masking an unavailable dependency.
An initial 99% target recognizes that this dependency is outside the service's direct control while still making
sustained upstream instability visible; it should be revisited as dependency reliability and operational history
become known.

## Latency

The latency SLI counts a request as good when its duration is at or below 0.16 seconds; all `/kb/search` requests
are valid. The objective is 99%, giving a 1% bad-request fraction and the same 432 budget-equivalent minutes over
30 days.

The measured service p99, 0.157725634 seconds, is 2.274 milliseconds below the threshold. The direct `kb-index`
p99, 0.149969915 seconds, is close to the 0.15-second boundary; the service p99 is about 7.756 milliseconds
higher, consistent with some additional endpoint overhead while remaining near the dependency's latency. The
0.16-second threshold is a finite histogram boundary, so Prometheus can count qualifying requests directly. It is
a deliberately close, provisional target: the observed p99 supports it, but the small margin means sustained
regressions should consume budget and prompt review rather than be hidden by a loose threshold. These two p99
measurements alone do not describe the median or the shape of the full latency distribution.

## Alerts

| alert | SLI | burn rate | long / short window | budget spent when it fires | severity: page or chat |
|---|---|---|---|---|---|
| `KbSearchLatencyFastBurn` | latency | 14.4 | 1h / 5m | 2% over the 1h long window | P1 — page |
| `KbSearchLatencySlowBurn` | latency | 6 | 6h / 30m | 5% over the 6h long window | P2 — chat |

The fast alert is intended to page when both windows show a very rapid latency-budget burn: at 14.4 times the
allowed bad-request rate, about 14.4% of requests exceed 0.16 seconds, and a sustained hour at that rate spends
2% of the 30-day budget. This level warrants immediate investigation rather than waiting for office hours. The
slow alert is intended for chat when a less extreme but persistent 6x burn is present in both windows; six hours
at that rate spends 5% of the budget. Chat notification avoids waking someone for the lower urgency signal while
making a continuing degradation visible for timely follow-up. Requiring both long and short windows makes each
alert sensitive to sustained consumption while reducing reactions to brief spikes.

The alert names, SLI, burn rates, and windows are the intended contract for the corresponding Prometheus rules;
the rule file must define matching multi-window expressions and severity labels for these entries.

## Buckets

The histogram concentrates boundaries near the measured tail, including 0.14, 0.15, 0.16, 0.17, and 0.18 seconds,
while extending to both much faster requests and a longer latency tail. The service p99 of 0.157725634 seconds
falls in `(0.155, 0.16]`, a 5 ms-wide bucket or about 3.17% of p99. The dependency p99 of 0.149969915 seconds
falls in `(0.145, 0.15]`, also 5 ms wide or about 3.33% of its p99. Both widths are well within the Lab 3
resolution criterion of 20% of the measured p99, and the threshold boundary at 0.16 seconds also supports an
exact latency SLI count without quantile interpolation.
