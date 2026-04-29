<!-- install:start -->
```bash
# Install with your preferred provider:
pip install "agentsuite[anthropic] @ git+https://github.com/scottconverse/AgentSuite.git"   # Anthropic Claude
pip install "agentsuite[openai] @ git+https://github.com/scottconverse/AgentSuite.git"      # OpenAI GPT
pip install "agentsuite[gemini] @ git+https://github.com/scottconverse/AgentSuite.git"      # Google Gemini
pip install "agentsuite[ollama] @ git+https://github.com/scottconverse/AgentSuite.git"      # Local Ollama daemon

# Install everything:
pip install "agentsuite[all] @ git+https://github.com/scottconverse/AgentSuite.git"

# or, no install (MCP only):
uvx --from "agentsuite[mcp] @ git+https://github.com/scottconverse/AgentSuite.git" agentsuite-mcp
```
<!-- install:end -->
