# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

Security vulnerabilities can be reported via:

- Email: security@example.com
- GitHub Security Advisory: [Report a vulnerability](https://github.com/muah1987/ollama-cli/security/advisories/new)

Please include:
- Description of the vulnerability
- Steps to reproduce (if applicable)
- Impact assessment
- Proposed fix (if known)

## Security Best Practices

### API Keys

Never commit API keys to the repository. Use environment variables:

```bash
export ANTHROPIC_API_KEY="your-key"
export GEMINI_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
```

### Environment Variables

All sensitive configuration should use environment variables, not hardcoded values.

### Output Validation

Always validate and sanitize user input before processing.

### HTTPS

Always use HTTPS when connecting to cloud providers.

### Local Server

The local Ollama server should be configured to:
- Accept connections only from localhost
- Use authentication if exposed to the network

---

## Current Security Posture

- API keys are read from environment variables only
- No data is logged from API calls
- All connections to cloud providers use HTTPS
- No sensitive data is stored in the repository

---

## Dependencies

We actively maintain dependencies and update them regularly. Security updates are prioritized.