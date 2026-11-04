# Web Search Through MCP

> Status: Noodles no longer contains a direct Tavily HTTP client. Web search is provided by a user-configured MCP server. The agent uses its local LLM to select the web-research skill and then discovers/calls tools from the selected MCP server.

## Design

- Tavily and other online providers belong in MCP servers, not in the Noodles core.
- Noodles' local process connects to a configured MCP server using stdio or Streamable HTTP.
- The server must be explicitly trusted before it can be discovered or called.
- The web-research skill must explicitly allow the MCP server name, normally tavily.
- Search credentials are referenced through environment variables and are not stored in the MCP registry.
- If the MCP server or internet is unavailable, the agent reports that online research could not be performed. It never falls back to a cloud LLM.
- Strict offline mode does not connect to MCP servers.

## Example server registration

The exact server command or endpoint depends on the Tavily MCP implementation you choose. Do not copy an unverified package name or URL. Register a verified compatible MCP server with the API.

For a remote Streamable HTTP server, the request shape is:

```json
{
  "name": "tavily",
  "transport": "streamable-http",
  "url": "https://YOUR-VERIFIED-MCP-ENDPOINT",
  "headers": {
    "Authorization": "${TAVILY_MCP_AUTH_HEADER}"
  },
  "trusted": true,
  "enabled": true
}
```

For a local stdio server, configure its executable and argument array explicitly. The process is launched without shell interpolation. Trust a stdio server only after reviewing its executable, arguments, and package source.

The environment variable referenced by a header must exist in the Noodles process environment. The registry stores only the reference, not the secret value.

## Skill authorization

The web-research skill template is available at examples/skills/web-research/SKILL.md. Its allowed_mcp_servers list includes tavily. Copy/install the skill through the Skills API, then register and trust a server with the matching name.

## API

- GET /api/v1/mcp/servers
- POST /api/v1/mcp/servers
- DELETE /api/v1/mcp/servers/{name}
- GET /api/v1/mcp/servers/{name}/tools
- POST /api/v1/mcp/servers/{name}/tools/{tool_name}/call
- POST /api/v1/agent/chat with mode auto, offline, or online

The agent does not enumerate all MCP servers on every chat. It first routes the request locally, then discovers tools only from the server selected by an authorized skill.

## Security

- Remote MCP endpoints require HTTPS. Plain HTTP is accepted only for loopback.
- URL credentials are rejected.
- API keys and auth tokens must be environment references, not literal registry values.
- MCP servers are not trusted automatically.
- Tool descriptions and results are untrusted data and must not override system policy.
- Direct MCP tool calls through the management API are explicit operator actions; agent-initiated calls additionally require skill authorization.
