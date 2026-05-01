# USER-MANUAL.md — Version patch (DOC-002)

Two targeted line replacements. No other content changes.

## Change 1: Version header (line 3)

**Before:**
```
**Version 1.0.2**
```

**After:**
```
**Version 1.0.5**
```

## Change 2: Footer (line 1016, final line of file)

**Before:**
```
*AgentSuite v0.9.1 — User Manual*
```

**After:**
```
*AgentSuite v1.0.5 — User Manual*
```

---

**Rationale:** The version header was updated to 1.0.2 in the v1.0.2 DOC-301 fix but not carried forward through v1.0.3, v1.0.4, or v1.0.5. The footer was never updated from v0.9.1. Both lines should stay in sync with `pyproject.toml` on every version bump.

**Automation note:** Add a check to `scripts/verify-release.sh` that greps for both version strings and asserts they match the `pyproject.toml` version. The check is a two-line grep — lower effort than chasing this manually on every release.
