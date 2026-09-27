# Vireo Support Analyzer

This is a small, zero-dependency Python tool for the Vireo Audio support-ticket task.

## Run

From this folder, run:

```text
python app.py
```

The command creates an `output` folder containing:

- `weekly_digest.csv`: issue counts and repeat counts by week
- `leaderboard.csv`: weekly tickets closed by non-warranty agents
- `action_recommendations.md`: evidence-based issue prioritization and next action
- `impact.txt`: the measurable business goal and cost scenario
- `validation.txt`: deduplication and classifier checks
- `memo.md`: the one-page business memo

## Decisions

The helpdesk row is preferred when the same ticket ID appears in both `helpdesk` and `legacy_fd`, because the email says the older data was re-imported. The digest uses the supplied structured category as its primary issue label. A fixed, explainable keyword tag is also computed as a secondary experiment and measured in `validation.txt`. Repeat contact is a practical proxy: the same customer and issue returning within 30 days after the previous resolution.

The leaderboard reports workload only. It excludes agents whose roster team contains `Warranty` or `Escalations`, following the support policy. Blank CSAT is not treated as zero.

No paid model calls are used, so the tool's AI inference cost is Rs 0. The trade-off is that multi-issue or unusually worded tickets can receive the wrong single tag.

The action brief is deterministic. It aggregates the digest, calculates issue share and repeat-contact rate, ranks issues by their sum, maps the selected issue to an operational owner, and states a metric to monitor. It does not claim that the recommendation proves root cause.