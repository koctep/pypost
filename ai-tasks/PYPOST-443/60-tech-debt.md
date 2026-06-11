# PYPOST-443: Technical Debt and Review (STEP 6)

## Delivered scope

- Deprecated alias `email_notification_failures_total` mirrors `request_retry_exhaustions_total`
  in `track_request_retry_exhaustion`.
- Operator migration guide with rollout checklist and PromQL examples.
- Tests assert dual export on registry scrape.
- Dev docs index updated.

## Technical debt findings

| Item | Severity | Status |
| ---- | -------- | ------ |
| Remove deprecated alias after sunset | Low | Follow-up — see below |
| `doc/dev/testing.md` metric table omits retry exhaustion series | Low | Non-blocker; covered in migration doc |

**Blockers:** None. **Verdict: SAFE TO CLOSE.**

## Follow-up recommendations

1. **Alias removal (Debt):** Jira:
   [PYPOST-558](https://pypost.atlassian.net/browse/PYPOST-558) — after sunset window (see
   migration doc), remove `_legacy_email_notification_failures_total` and dual increment; update
   tests and migration doc to historical-only.
2. **Operations:** Run rollout checklist; confirm all Grafana/alert queries migrated to
   canonical name before alias removal release.

## Risk assessment

| Risk | Mitigation |
| ---- | ---------- |
| Operators never migrate off legacy name | Documented sunset; follow-up Jira for removal |
| Confusion between two identical series | Migration doc explains mirror semantics |
| Permanent dual export | Sunset + follow-up task |
