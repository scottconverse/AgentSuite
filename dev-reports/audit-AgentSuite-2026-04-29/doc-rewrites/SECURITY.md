# Security Policy

## Supported versions

AgentSuite is a single-maintainer open-source project. Security fixes land on the latest released minor version. Older minor versions are not patched.

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0.0 | No        |

## Reporting a vulnerability

**Do not open a public issue for a security vulnerability.**

Please use GitHub Security Advisories: <https://github.com/scottconverse/AgentSuite/security/advisories/new>

If GitHub Security Advisories is not available to you, contact the maintainer through the channel listed at <https://github.com/scottconverse>.

### What to include

- A description of the vulnerability and its impact.
- Reproduction steps (AgentSuite version, Python version, OS, configuration).
- A proposed fix (optional).

### Response commitments

- **Acknowledgement** within 5 business days.
- **Initial assessment** within 10 business days.
- **Fix or mitigation timeline** communicated within the initial assessment window. AgentSuite is small enough that fixes ship within days for any Critical-severity report.

## Scope

**In scope:**
- The `agentsuite` Python package (CLI, library API, MCP server).
- The kernel pipeline, state store, and artifact writer.
- Provider integrations under `agentsuite.llm.*`.
- The release pipeline (`.github/workflows/`).

**Out of scope:**
- Vulnerabilities in upstream LLM providers (Anthropic, OpenAI, Google, Ollama). Report to the provider directly.
- Vulnerabilities in user prompts or LLM-generated artifacts. AgentSuite orchestrates LLM calls; it does not vet model output for security claims.
- Issues that require physical access to a developer machine running AgentSuite.

## Disclosure

Once a fix is released, the maintainer will publish a GitHub Security Advisory and credit the reporter (with their consent). The CycloneDX SBOM attached to each release identifies the dependency closure that was audited; reporters can verify the fix by downloading the post-fix SBOM.

## Supply-chain hygiene

Every tagged release runs `pip-audit --strict` against the freshly built wheel and attaches a CycloneDX JSON SBOM to the GitHub Release (per CHANGELOG v0.8.3). A weekly provider-drift workflow (`.github/workflows/provider-drift.yml`) confirms the model names in `agentsuite/llm/pricing.py` are still listed by each provider.
