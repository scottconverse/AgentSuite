# PatentForgeLocal (frozen fixture for AgentSuite Founder golden test)

PatentForgeLocal is a Windows-installable patent drafting tool that runs entirely on the user's local machine. It bundles a portable Python runtime and Ollama with the gemma model. The installer is built with Inno Setup 6.x and currently ships unsigned. There is no Docker or WSL dependency.

The product is for independent inventors, solo founders, and small IP firms that want to draft provisional patent applications without sending sensitive disclosures to a cloud LLM.

What it does:
- Drafts patent claims, abstract, summary, and figure descriptions from a one-page invention disclosure
- Runs offline once installed
- Maintains a local sqlite database of drafts and revisions

What it does not do:
- File patents with the USPTO
- Replace a registered patent attorney
- Generate art-quality figures (only mechanical line drawings)
