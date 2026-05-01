# CHANGELOG.md — Footer comparison links replacement (DOC-004)

Replace the entire footer link block at the bottom of CHANGELOG.md (currently lines 590–604)
with the block below. This adds all missing version comparison links from v0.9.2 through v1.0.5
and corrects the `[Unreleased]` anchor to point at v1.0.5...HEAD.

---

## Current (broken) block to replace:

```
[Unreleased]: https://github.com/scottconverse/AgentSuite/compare/v0.9.1...HEAD
[0.9.1]: https://github.com/scottconverse/AgentSuite/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/scottconverse/AgentSuite/compare/v0.8.4...v0.9.0
[0.8.4]: https://github.com/scottconverse/AgentSuite/compare/v0.8.3...v0.8.4
[0.8.3]: https://github.com/scottconverse/AgentSuite/compare/v0.8.2...v0.8.3
[0.8.2]: https://github.com/scottconverse/AgentSuite/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/scottconverse/AgentSuite/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/scottconverse/AgentSuite/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/scottconverse/AgentSuite/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/scottconverse/AgentSuite/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/scottconverse/AgentSuite/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/scottconverse/AgentSuite/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/scottconverse/AgentSuite/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/scottconverse/AgentSuite/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/scottconverse/AgentSuite/releases/tag/v0.1.0
```

## Replacement block:

```
[Unreleased]: https://github.com/scottconverse/AgentSuite/compare/v1.0.5...HEAD
[1.0.5]: https://github.com/scottconverse/AgentSuite/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/scottconverse/AgentSuite/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/scottconverse/AgentSuite/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/scottconverse/AgentSuite/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/scottconverse/AgentSuite/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/scottconverse/AgentSuite/compare/v1.0.0rc1...v1.0.0
[1.0.0rc1]: https://github.com/scottconverse/AgentSuite/compare/v0.9.3...v1.0.0rc1
[0.9.3]: https://github.com/scottconverse/AgentSuite/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/scottconverse/AgentSuite/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/scottconverse/AgentSuite/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/scottconverse/AgentSuite/compare/v0.8.4...v0.9.0
[0.8.4]: https://github.com/scottconverse/AgentSuite/compare/v0.8.3...v0.8.4
[0.8.3]: https://github.com/scottconverse/AgentSuite/compare/v0.8.2...v0.8.3
[0.8.2]: https://github.com/scottconverse/AgentSuite/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/scottconverse/AgentSuite/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/scottconverse/AgentSuite/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/scottconverse/AgentSuite/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/scottconverse/AgentSuite/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/scottconverse/AgentSuite/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/scottconverse/AgentSuite/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/scottconverse/AgentSuite/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/scottconverse/AgentSuite/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/scottconverse/AgentSuite/releases/tag/v0.1.0
```

---

**Automation note:** In `scripts/verify-release.sh`, add a step that extracts the latest version
from `pyproject.toml` and verifies `[Unreleased]: .../compare/v<VERSION>...HEAD` appears in the
CHANGELOG footer. This is a two-line grep and prevents this from drifting again.
