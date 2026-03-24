# Tech debt files vs Jira — manager review (remediation list)

Review after junior linked `40-tech-debt.md` / `60-tech-debt.md` items to Jira. Spot-checks
against Jira (e.g. PYPOST-253, PYPOST-341, PYPOST-352, PYPOST-125, PYPOST-386) show **issue
summaries mirror the first line of the markdown bullet**, including **mid-sentence cuts**.

## 1. Markdown source (`ai-tasks/**/40-tech-debt.md`, `60-tech-debt.md`)

### 1.1 Broken line wrapping (highest priority)

Many list items were hard-wrapped at ~100 characters **before** the em dash and Jira link. The
line therefore ends on a dangling word (`using`, `without a`, `Tests`, `relied`, `for`, `and`,
`a`, `due to absent`, etc.). That violates readable prose (see `.cursor/lsr/do-markdown.md`) and
produced useless Jira titles.

**Fix:** Reflow each bullet so the full sentence (or a clear clause) stays coherent. Acceptable
patterns:

- Put the link on its own continuation line after a complete sentence, or
- Shorten the lead-in, or
- Use a **bold short label** plus a wrapped body (as in `PYPOST-53/60-tech-debt.md`), or
- Split into sub-bullets.

**Scope:** Essentially all `60-tech-debt.md` files under `PYPOST-25`–`PYPOST-42` (and matching
`40-tech-debt.md` entries) that use the `… — [PYPOST-…](url)` pattern with a truncated first
line. Same pattern appears in `PYPOST-13`, `PYPOST-14`, `PYPOST-18`, `PYPOST-27`, etc.

### 1.2 Link separated from the rest of the bullet

**File:** `ai-tasks/PYPOST-42/60-tech-debt.md` (Missing Tests)

The Jira link sits at the end of the first physical line while the explanation continues on the
next line, so the markdown source reads as if the ticket were only about “Would require”.

**Fix:** Merge into one logical bullet: full text first, then `— [PYPOST-385](…)` on the same
line as the sentence end, or restructure (e.g. two sentences, link after the second).

### 1.3 Placeholder text in a live bullet

**File:** `ai-tasks/PYPOST-13/40-tech-debt.md`

- **Resolved:** Markdown already used the correct wording (no `PYPOST-XX`). **PYPOST-124** in Jira
  was updated so Summary and Description match the bullet (removed stale `(PYPOST-XX)` text).

### 1.4 Inconsistent list semantics (`- [ ]` vs `-`)

Several `40-tech-debt.md` files mix **task checkboxes** (`- [ ]`) with Jira links (`PYPOST-23`,
`PYPOST-29`, `PYPOST-13`, …). Unclear whether checkboxes are synced with Jira workflow.

**Fix:** Agree one convention: either plain bullets + Jira as source of truth, or checkboxes only
for items **without** a Jira issue. Update docs accordingly.

### 1.5 Inconsistent linking style

- `PYPOST-53/60-tech-debt.md`: numbered items with link inside the heading text — readable.
- Most other files: long bullets with trailing `— [KEY](url)` — often broken by line wrap.

**Fix:** Standardize on one pattern for new/edited files (recommend the PYPOST-53 style for dense
items).

## 2. Jira (after markdown is fixed)

### 2.1 Truncated summaries

For bulk-created issues, **Summary** often ends mid-phrase (confirmed for PYPOST-253, PYPOST-341,
PYPOST-352, PYPOST-125, PYPOST-386). Descriptions frequently contain the full text.

**Fix:** Rewrite **Summary** to a standalone, imperative or noun-phrase title (under Jira length
limits). Pull wording from the description’s first complete sentence, not from the old markdown
line fragment.

### 2.2 Summary naming inconsistency

- Some issues: `[PYPOST-N] …` prefix with truncated remainder.
- Others (e.g. PYPOST-54–PYPOST-56): clean titles without the bracket prefix.

**Fix:** Pick one team convention (prefix vs no prefix) and align backlog grooming.

## 3. Backlog / product hygiene

### 3.1 Near-duplicate narratives

Multiple stories reuse the same Makefile / flake8 / pytest / save-widget narrative with
**different** keys (e.g. `PYPOST-27` vs `PYPOST-30` vs `PYPOST-33` `60-tech-debt.md`; `PYPOST-26`
vs `PYPOST-29` for the “+” tab button block; `PYPOST-25` vs `PYPOST-28` vs `PYPOST-31` for
save-related debt).

**Fix:** Product owner should decide: link duplicates to one **epic** or canonical issue, use
**relates to** / **duplicates**, or accept parallel per-story tickets — but avoid confusing the
team with many identical-sounding tasks.

## 4. Suggested verification (junior / QA)

1. Re-open a random sample of linked issues per file: summary readable without opening
   description.
2. Grep for lines matching ` — \[PYPOST-` where the text before `—` ends with a short function
   word (`a`, `the`, `for`, `and`, `using`, …) — likely still broken.
3. Grep for `PYPOST-XX` in `ai-tasks`.

---

*Jira spot-check performed via project MCP search on keys PYPOST-54, PYPOST-55, PYPOST-56,
PYPOST-125, PYPOST-247, PYPOST-253, PYPOST-341, PYPOST-352, PYPOST-386.*
