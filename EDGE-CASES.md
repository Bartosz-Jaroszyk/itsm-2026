---
lab2_edge_cases:
  E1: {rule: R-08, count: 3}
  E2: {rule: R-06, count: 2}
  E3: {rule: R-09, count: 4}
  E4: {rule: R-10, count: 4}
  E5: {rule: R-12, count: 1}
  E6: {rule: R-13, count: 11}
---
<!-- ai-generated: 80% - Copilot drafted explanations from the Lab 2 specification and practice fixture -->

# Edge cases in the practice event log

The declared counts below are the values returned by this service for the published practice fixture.

| declare here | service field |
|---|---|
| E1 | `anomalies.negative_lead_time_pairs` |
| E2 | `anomalies.revert_chains_collapsed` |
| E3 | `anomalies.commits_never_on_main` |
| E4 | `anomalies.deployments_without_commits` |
| E5 | `counts.open_failures` |
| E6 | `anomalies.overlapping_incident_pairs` |

## E1 - clock skew produces a negative lead time

- What the log contains: Three shipped commit timestamps fall after their first successful deployments, producing negative lead-time pairs.
- What a default definition would have done: A naive calculation would report negative durations or discard the skewed pairs from the median.
- Why the rule is defensible: Clamping each duration to zero preserves every shipped commit in the metric and avoids credit for negative elapsed time.

## E2 - a revert of a revert

- What the log contains: Two commits have non-null `reverts`; the later revert points to an earlier revert rather than creating its own change.
- What a default definition would have done: A simplistic implementation might count revert commits as new changes or stop following the chain after one link.
- Why the rule is defensible: Following revert ancestry transitively attributes the work to its original change and avoids inflating change counts.

## E3 - a hotfix that never touched `main`

- What the log contains: Four distinct shas carried by production deployments in the window have a branch value other than `main`.
- What a default definition would have done: A main-only interpretation could omit hotfix work from delivery metrics and undercount these commits.
- Why the rule is defensible: Production delivery is the observable outcome; branch names do not determine whether deployed work reached users.

## E4 - a deployment with zero linked commits

- What the log contains: Four in-window production deployments have empty `commits` arrays, including deployments with different outcomes.
- What a default definition would have done: A naive implementation might discard empty deployments from the denominator or treat them as malformed.
- Why the rule is defensible: The deployment still occurred and must affect frequency and deployment-rate denominators even without linked commit data.

## E5 - a deployment that failed and never recovered

- What the log contains: One in-window production failure has no covering incident with a resolution event, so its recovery duration is unknown.
- What a default definition would have done: A naive calculation might invent a recovery time, use the observation-window end, or omit the failure entirely.
- Why the rule is defensible: Leaving the failure open keeps the recovery median limited to observed recoveries while retaining the failure in the fail-rate denominator.

## E6 - overlapping incidents

- What the log contains: Eleven unordered pairs of distinct incident intervals intersect in the practice log.
- What a default definition would have done: A simplistic approach could merge intersecting incidents or add their durations together as if they were one outage.
- Why the rule is defensible: Incident records remain distinct, and interval intersection can be counted without distorting per-deployment recovery measurements.

## Gaming demonstration

No gaming demonstration is included here, so this file does not claim that a metric was improved or that a rule was exploited.
