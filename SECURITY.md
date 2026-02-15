# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |

## Reporting a Vulnerability

If you discover a security vulnerability in Qarin CLI, please report it responsibly.

**Do not open a public issue.** Instead, email the maintainer directly or use GitHub's private vulnerability reporting feature.

### What to include

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to expect

- Acknowledgement within 48 hours
- A fix or mitigation plan within 7 days for critical issues
- Credit in the release notes (unless you prefer to remain anonymous)

## Security Considerations

Qarin CLI executes shell commands and reads/writes files on behalf of the user through its agent tools. Keep the following in mind:

- **API keys** -- Store `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` in environment variables or `.env` files. Never commit them to version control.
- **Tool execution** -- The agent's `shell_exec` and `file_write` tools operate with the same permissions as the user running the CLI. Review tool actions before confirming execution.
- **Network requests** -- The `web_fetch` tool makes outbound HTTP requests. Be aware of what URLs the agent is accessing.
- **Session data** -- Sessions saved in `.qarin/sessions/` may contain conversation history. Treat these files as sensitive if your prompts include confidential information.
