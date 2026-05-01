# USER-MANUAL.md — ConsistencyCheckFailed replacement patch (DOC-003)

As of v1.0.3, `ConsistencyCheckFailed` no longer exists as an exception. The pipeline now
continues to the approval step and sets `requires_revision=True` when consistency issues are
found. The error row in every agent's "Common errors" table must be updated.

---

## Replace in all 7 agent chapters: "Common errors" table row

**Find (appears 7 times, one per agent chapter):**
```
| `ConsistencyCheckFailed` | Two documents contradict each other | Make your `--business-goal` more specific, then re-run |
```
(The third column varies slightly by agent — "Make your `--design-brief` more specific",
"Make your `--campaign-goal` and `--target-market` descriptions more specific", etc.
Replace all variants.)

**Replace with:**
```
| Consistency issues in `consistency_report.json` | The consistency check found cross-artifact contradictions. The pipeline completed; `requires_revision=True` is set in the run state. | Open `.agentsuite/runs/<run-id>/consistency_report.json`. Review the `mismatches` list. Approve and edit documents by hand, or re-run with more specific inputs. |
```

---

## Section 10 (Troubleshooting) — remove or update the ConsistencyCheckFailed entry

**Find:**
```
**`ConsistencyCheckFailed`**

Two of the nine documents produced by the agent contradict each other — for example, the target audience described in one document does not match the target audience in another. This usually means your inputs were ambiguous.

Fix: make your required inputs more specific. For example, instead of `--target-users "entrepreneurs"`, try `--target-users "first-time founders building B2B SaaS products with less than $1M in funding."` Then re-run.
```

**Replace with:**
```
**Consistency issues flagged in output**

The consistency check at Stage 3 found contradictions between documents — for example, two documents targeting different audiences. As of v1.0.3, this does not halt the pipeline. The agent completes all five stages, and the run enters the approval state with `requires_revision=True`.

What to do:
1. Open `.agentsuite/runs/<run-id>/consistency_report.json`. The `mismatches` list names the documents involved and describes what contradicts what.
2. You can approve and edit the flagged documents by hand, or re-run with more specific inputs (for example, a more precise `--target-users` or `--business-goal`).
3. If the contradictions are severe, re-running with more specific inputs typically produces a cleaner result on the first attempt.
```

---

## Glossary — update the ConsistencyCheckFailed entry

**Find:**
```
**ConsistencyCheckFailed:** An error that occurs when two of the nine documents produced by an agent contradict each other. The fix is to make your inputs more specific and re-run.
```

**Replace with:**
```
**Consistency check:** A cross-artifact check that runs at the end of Stage 3 (Spec). If it finds contradictions between documents, the pipeline continues but sets `requires_revision=True` in the run state. Review `consistency_report.json` in the run folder to see what was flagged. As of v1.0.3, this check no longer halts the pipeline.
```

---

**Why these changes matter:** A user on v1.0.3 or later who searches for `ConsistencyCheckFailed` in the manual finds an entry that describes a behavior that no longer exists. The replacement guides them to the actual post-v1.0.3 recovery path (inspect `consistency_report.json`, then approve or re-run).
