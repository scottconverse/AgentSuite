"""Downstream-consumer typing test — PEP 561 / py.typed marker validation.

Synthesizes a small package that imports AgentSuite's public surface, runs
mypy against it, and asserts a clean type-check. This is the rc1 compatibility
gate for users who type-check their own code against AgentSuite.

The test is intentionally narrow: it exercises the specific import paths
that downstream code is expected to use. Adding a new public type? Add it
to the consumer fixture below.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


CONSUMER_SOURCE = textwrap.dedent('''
    """Synthetic downstream consumer of AgentSuite's public API."""
    from __future__ import annotations

    from pathlib import Path

    from agentsuite.agents.founder.agent import FounderAgent
    from agentsuite.agents.founder.input_schema import FounderAgentInput
    from agentsuite.kernel.schema import Constraints
    from agentsuite.kernel.qa import QARubric, RubricDimension
    from agentsuite.llm.base import LLMProvider
    from agentsuite.llm.mock import MockLLMProvider


    def make_input(slug: str) -> FounderAgentInput:
        """Build a typed FounderAgentInput from a slug."""
        return FounderAgentInput(
            agent_name="founder",
            role_domain="creative-ops",
            user_request="downstream test",
            business_goal="ensure downstream typing works",
            project_slug=slug,
            constraints=Constraints(),
        )


    def run_with(llm: LLMProvider, out: Path, slug: str) -> str:
        """Run a Founder agent with a typed LLM provider; return run id."""
        agent = FounderAgent(output_root=out, llm=llm)
        state = agent.run(request=make_input(slug), run_id="downstream-1")
        return state.run_id


    def make_rubric() -> QARubric:
        """Construct a QARubric using only public types."""
        return QARubric(
            dimensions=[
                RubricDimension(name="x", question="x?"),
            ],
            pass_threshold=7.0,
        )


    if __name__ == "__main__":
        rubric = make_rubric()
        provider: LLMProvider = MockLLMProvider({})
        run_id = run_with(provider, Path("/tmp"), "consumer-test")
        print(rubric, provider, run_id)
''')


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_downstream_consumer_typechecks_clean(tmp_path: Path) -> None:
    """A synthetic consumer using AgentSuite's public API must type-check clean.

    Editable installs (`pip install -e .`) hide the source tree behind a
    `.pth` file that mypy does not follow. We point mypy at the repo via
    `MYPYPATH` so the consumer resolves AgentSuite's typed source — exactly
    what a downstream consumer with a non-editable install would see via
    the package's `py.typed` marker.
    """
    import os

    consumer = tmp_path / "consumer_pkg"
    consumer.mkdir()
    (consumer / "__init__.py").write_text("", encoding="utf-8")
    (consumer / "consumer.py").write_text(CONSUMER_SOURCE, encoding="utf-8")

    env = dict(os.environ)
    env["MYPYPATH"] = str(REPO_ROOT)

    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", "--ignore-missing-imports", str(consumer)],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=env,
    )

    msg_lines = [
        "mypy --strict failed against synthetic downstream consumer.",
        "stdout:",
        result.stdout,
        "stderr:",
        result.stderr,
    ]
    assert result.returncode == 0, "\n".join(msg_lines)
