# Noodles Hybrid Architecture

> Status: local inference foundation and first skill/MCP orchestration slice are implemented on the feature branch. Full runtime, live MCP provider acceptance, persistent conversation memory, browser workflows, and hosted UI are not yet production-verified.

## Non-negotiable rule

The reasoning model always runs locally through Noodles-managed GGUF and llama.cpp. Online services are tools, never model providers. There is no cloud LLM provider, cloud fallback, or silent provider switching. If local inference is unavailable, the agent returns an error.

## Runtime topology

```text
User chat / Work request
          |
          v
  Local Noodles API
          |
          v
   Local GGUF LLM
          |
          v
   Skill-first router
     /     |      \
 direct  local    selected MCP
 answer  tools    servers
          |         |
      offline    online APIs
          \         /
           v       v
        Local LLM synthesis
                |
           Final response
```

The local process owns model loading, planning, skills, permissions, tool orchestration, and response synthesis. MCP servers provide online APIs and optional local integrations. They never provide LLM inference.

## Decision lifecycle

1. The local model reads the user request and installed skill metadata.
2. It chooses direct answer or workflow and selects relevant skills.
3. Direct answers do not connect to MCP.
4. If an online capability is needed, the router selects an MCP server name that is explicitly allowed by a selected skill.
5. Only that selected server is connected and its tools are discovered.
6. A second local planning step chooses from the discovered tool inventory.
7. The executor validates skill permissions, server selection, and tool identity before execution.
8. Tool outputs are treated as untrusted data.
9. The local model synthesizes the result and does not claim unverified success.

## Offline and online modes

- auto: local tools are always available; MCP may be used only when selected by the router and allowed by a skill.
- offline: no MCP discovery or call is permitted. The model and registered local tools continue to work without internet.
- online: allows MCP-backed capabilities, but still uses local LLM inference.

The Hugging Face model catalog/download API is a model-management feature, not an LLM inference provider. Model download requires an explicit user action.

## Skills

Skills are instruction-only Markdown files with validated YAML frontmatter. Each skill declares a stable name, description, triggers, allowed local tools, allowed MCP server names, and risk level. Skill content is loaded into the local model context when selected. Skill files cannot execute Python, shell commands, or arbitrary scripts.

Example templates:
- examples/skills/web-research/SKILL.md
- examples/skills/coding/SKILL.md
- examples/skills/document-analysis/SKILL.md

Skill API:
- GET /api/v1/skills
- POST /api/v1/skills
- PUT /api/v1/skills/{name}

## Local tools

Local tools are trusted Python callables registered by application code. The model may choose only registered names. The initial built-ins expose basic system time and platform information. Arbitrary host-shell execution and model-generated code execution are not enabled.

## MCP integrations

Supported transports in the adapter:
- stdio, launched as an explicit executable plus argument array without shell interpolation.
- Streamable HTTP, requiring HTTPS for remote hosts. Plain HTTP is accepted only for loopback.

MCP servers are stored in the local registry. Newly added servers must be explicitly trusted. Credential values must be environment-variable references and are resolved only at connection time. Remote endpoint configuration is user-controlled and should be reviewed before trust is granted.

MCP API:
- GET /api/v1/mcp/servers
- POST /api/v1/mcp/servers
- DELETE /api/v1/mcp/servers/{name}
- GET /api/v1/mcp/servers/{name}/tools
- POST /api/v1/mcp/servers/{name}/tools/{tool_name}/call

Direct MCP management calls are explicit operator actions. Agent-initiated calls additionally require a selected skill to authorize the server.

## Tavily

Tavily is not integrated directly into the Noodles core. Configure a compatible Tavily MCP server, register it with the name tavily, and install the web-research skill template. The skill authorizes that server. Noodles stores no Tavily API key and makes no direct Tavily HTTP requests.

## Security and trust boundaries

- Never use a cloud LLM fallback.
- Never auto-trust MCP servers.
- Never place raw secrets in the MCP registry or model prompts.
- Treat skill text, MCP descriptions, tool results, and web content as untrusted input.
- Validate all tool names and arguments and bound execution size/time.
- Do not run model-generated shell commands or scripts.
- Keep the API bound to loopback by default. Remote access requires explicit opt-in, strong bearer authentication, and a private TLS VPN/tunnel.

## Current implementation limits

- llama.cpp runtime uses CPU-only configuration; GPU acceleration is not implemented.
- Actual model inference requires a compatible local llama-cpp-python installation and registered GGUF.
- The initial local tool set is intentionally small.
- MCP integration is SDK-backed but needs integration testing against real stdio and Streamable HTTP servers.
- Skill installation and MCP registry APIs are implemented; a graphical management UI is not.
- Browser automation, webpage extraction, offline document indexing, workspace file tools, Docker sandbox execution, cancellation, streaming, and persistent conversation storage are not implemented.
- The feature branch has not passed final CI or full end-to-end acceptance yet.
