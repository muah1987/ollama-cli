# Contributing to Qarin CLI

Thank you for your interest in contributing to Qarin CLI. This guide will help you get started.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/<your-username>/qarin-cli.git
   cd qarin-cli
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Create a branch for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Running Locally

```bash
npm run dev          # Start with file watching
```

### Building

```bash
npm run build        # Compile TypeScript
npm run build:binary # Build standalone binary (requires Bun)
```

### Testing

```bash
npm run test         # Run Node.js tests
npm run test:py      # Run Python tests
npm run lint         # Type check with tsc --noEmit
```

### Before Submitting

1. Run `npm run lint` and fix any type errors
2. Run `npm run test` and ensure all tests pass
3. Test your changes manually with `npm run dev`

## Submitting Changes

1. Commit your changes with a clear message:
   ```bash
   git commit -m "feat: add new desert theme"
   ```
2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
3. Open a Pull Request against the `main` branch

### Commit Message Format

Use conventional commit prefixes:

| Prefix | Purpose |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code change that neither fixes a bug nor adds a feature |
| `test:` | Adding or updating tests |
| `chore:` | Maintenance tasks |

## What to Contribute

- **New themes** -- Add Arabic or culturally-inspired progress themes in `themes/`
- **Provider support** -- Add new LLM provider integrations in `core/models.js`
- **Tools** -- Add new agent tools in `core/tools.js`
- **Bug fixes** -- Check the issue tracker for open bugs
- **Documentation** -- Improve or translate docs

## Adding a Theme

Themes live in `themes/` and follow this structure:

1. Create a new file in `themes/` (e.g., `themes/bazaar.js`)
2. Export a theme object with phases: `analyzing`, `planning`, `implementing`, `testing`, `reviewing`, `complete`, `error`
3. Each phase should include `emoji`, `english`, and `arabic` message fields
4. Register your theme in `themes/index.js`

## Code Style

- TypeScript with strict types
- Use Zod for runtime validation where appropriate
- React components use the Ink library for terminal rendering
- Keep functions focused and well-named

## Reporting Bugs

Open an issue on GitHub with:

1. A clear title and description
2. Steps to reproduce
3. Expected vs actual behavior
4. Your environment (Node version, OS, provider used)

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
