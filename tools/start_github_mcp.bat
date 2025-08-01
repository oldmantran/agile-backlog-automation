@echo off
echo Starting GitHub MCP Server...
docker run -i --rm --env-file .env -e GITHUB_TOOLSETS=repos,issues,pull_requests ghcr.io/github/github-mcp-server stdio
pause 