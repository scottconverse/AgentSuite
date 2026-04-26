---
description: Run the AgentSuite Founder agent to produce a reusable creative-ops bundle (26 artifacts).
---

Invoke the founder-agent skill. If the user has provided arguments after `/founder-agent`, parse them as `--business-goal`, `--project-slug`, `--inputs-dir` overrides. Otherwise prompt for those three fields one at a time, then call `founder_run`.
