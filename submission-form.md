# Vireo Audio Submission Form

## What did you build, and what business outcome does it move?

I built a zero-dependency Python tool that removes migration duplicates, produces a weekly complaint digest, marks repeat contacts, and produces a weekly closure-volume leaderboard. It found 1,516 repeat-contact tickets out of 11,875 canonical tickets, or 12.8%. A 20% relative reduction in repeat contacts is the working goal. At the policy cost of Rs 290 per contact, that scenario is worth about **Rs 14,655 per quarter**.

The largest issue family was Delivery & Shipping with 2,134 tickets and 339 repeat contacts. The number is a target for operational action, not a guaranteed saving from the tool alone.

## What does one run cost, and what would a month cost at Vireo's volume?

No paid model calls are used. One run costs **Rs 0 in AI inference** and a month at roughly 650 tickets per week also costs **Rs 0** in AI inference:

`650 tickets/week x 4.33 weeks/month x Rs 0/ticket=Rs 0/month`

This excludes the user's own computer time and electricity.

## How do you know it works?

The raw export contains 12,528 rows and 11,875 distinct ticket IDs. The tool removed 653 duplicate rows by preferring the `helpdesk` row when one exists. A seeded sample of 200 tickets had 200/200 agreement between the digest label and the source structured category.

The independent keyword text tag agreed with the structured category on 117/200 tickets, an error rate of 41.5%. It is therefore not used as the primary digest label. It most often fails on vague messages and messages containing several issues.

## Did you change, narrow, or push back on the client's ask?

Yes. I kept the requested leaderboard but labelled it a **workload leaderboard**, not a performance ranking. The policy says Tier 2 warranty work is multi-touch and must not be compared with Tier 1 using closure volume, so warranty and escalation agents are excluded from the comparison.

I also defined repeat contact as a measurable proxy using the same customer and structured issue returning within 30 days after the previous resolution. This is explicit and reproducible, but it is not a perfect semantic match for “same issue”.

## What is wrong with what you are handing us?

- The digest depends on the exported category field, so it is not a fully independent understanding of free text.
- The experimental text tag is weak on multi-issue tickets.
- Duplicate handling chooses the first `helpdesk` row and does not reconcile every conflicting field.
- The repeat-contact rule uses category as an issue proxy and can miss differently worded versions of the same problem.
- The quarterly saving is a scenario based on a 20% reduction; it is not causal proof.
- There is no live helpdesk connection, alerting, authentication, or scheduled job.

## What did you deliberately leave out, and why?

I left out sentiment scoring, churn prediction, automatic routing, a real-time dashboard, and a quality-based agent score. They need additional labels or live operational integration and do not improve the requested weekly digest and cost case within the five-hour cap.

## Anything you built or found that nobody asked for?

I added an evidence-based action recommendation layer that combines issue volume and repeat-contact rate, identifies the top volume and top repeat-rate issues, maps the priority issue to a likely business owner, and names the metric to monitor. It answers what to investigate next without using an LLM or pretending to prove root cause. The generated brief is `output/action_recommendations.md`.

## What did you use AI for?

I used GitHub Copilot for code design, implementation, debugging, and writing this documentation. The finished tool uses Python's standard library and no paid model API. I discarded an early idea of sending every ticket to an LLM because it would add cost and make the categories harder to reproduce. I also kept the keyword tag as a measured experiment rather than hiding its 41.5% error rate.

Three-minute screen recording: **Not uploaded yet. Use `recording-script.md` to record the walkthrough and paste the public link here.**

## Public Google Drive Link

**Not uploaded yet.**

## Someone picks this up on Monday: three things they need to know

1. Run `python app.py`; all reports are regenerated in the `output` folder.
2. Do not count raw ticket rows. Use the canonical ticket IDs produced by the tool because 653 migration duplicates exist.
3. Treat the leaderboard as workload only, keep warranty agents separate, and review the repeat-contact definition before using the savings scenario for a decision.

## Honest hours spent

**5 hours**

## Github Repo Link

**Not uploaded yet.**