# Skills and MCP Architecture

## Core rule

The local LLM is the only reasoning model. Skills define workflows and operating procedures. Local tools provide offline capabilities. MCP servers provide external APIs and integrations. A skill may authorize a specific local tool or MCP server, but it never contains executable code.

## Request lifecycle

1. The local intent router reads the user request and installed skill metadata.
2. It selects direct-answer or workflow mode, relevant skills, and any candidate MCP server names.
3. Direct answers do not need to connect to MCP servers.
4. Only selected, skill-authorized MCP servers are discovered.
5. A second local planning step chooses from the discovered MCP tool inventory.
6. The executor validates each action against skill permissions and registered tools.
7. Tool outputs are treated as untrusted data.
8. The local LLM synthesizes the final answer and reports failed or unavailable actions honestly.

## Skill format

Skills are Markdown files named SKILL.md with YAML frontmatter. Metadata fields:

- name: stable lowercase identifier
- description: when the skill is relevant
- version: skill version
- triggers: example intent phrases
- allowed_tools: exact local tool names
- allowed_mcp_servers: exact registered MCP server names
- risk_level: low, medium, or high

Install/update skills through the API. Skills are instruction-only; scripts inside skills are not executed.

Example skill templates are in examples/skills/.

## Local tools

Local tools are registered in Python by trusted application code. The model can select only registered tool names. There is no dynamic Python evaluation, shell execution, or implicit host command capability.

## MCP server connections

Supported transports in the current adapter:

- stdio: launches a configured MCP process using explicit command and argument fields, without shell interpolation.
- streamable-http: connects to an HTTPS MCP endpoint. Plain HTTP is accepted only for loopback hosts.

MCP server registration is explicit. A server must be marked trusted before discovery or calls. Credentials and environment values are stored as environment-variable references, never as literal secrets in the MCP registry. The referenced environment variables must exist in the Noodles process environment.

MCP servers are separate from Noodles' model runtime. Add search, browser, databases, file services, and other APIs as MCP servers rather than adding provider-specific API clients to the core.

## Tavily

Tavily is an MCP integration, not a built-in Noodles search adapter. Install/configure a compatible Tavily MCP server, register it under the name tavily, and add tavily to the allowed_mcp_servers list of the web-research skill. Noodles itself does not store or call Tavily API keys.

## Security boundaries

- Never auto-trust a newly registered MCP server.
- Remote MCP endpoints must use HTTPS.
- Stdio servers execute local processes and must be trusted only when their command and arguments have been reviewed.
- MCP tool names and schemas are discovered from the connected server, not guessed.
- Skill permissions are checked before every call.
- Remote content and tool outputs are data, not instructions.
- Tool execution is bounded; arbitrary model-generated code is never executed.
- Strict offline mode must not connect to MCP servers.
