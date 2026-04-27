# Contributing to Epsimo CLI

Thanks for your interest in contributing! This guide covers how to set up the project, make changes, and submit them.

---

## Getting Started

### 1. Fork and clone

```bash
git clone https://github.com/<your-username>/epsimo-cli.git
cd epsimo-cli
```

### 2. Set up the development environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 3. Verify the installation

```bash
epsimo --version
python3 verify_skill.py
```

---

## Project Structure

```
epsimo-cli/
├── epsimo/              # Core package
│   ├── cli.py           # CLI entry point (argparse)
│   ├── cli_smart.py     # Smart commands (chat, exec, search, tools)
│   ├── tui.py           # Interactive TUI dashboard
│   ├── client.py        # SDK client
│   ├── auth.py          # Authentication
│   └── resources/       # Resource-specific SDK clients
├── scripts/             # Helper and test scripts
├── docs/                # Documentation
├── references/          # API reference
└── tests/               # Test files
```

---

## Making Changes

### Code style

- Follow existing patterns in the codebase
- Use type hints where practical
- Keep functions focused and small
- Add docstrings to public functions

### Commit messages

Use clear, descriptive commit messages:

```
feat: add /export slash command to TUI chat
fix: handle expired token in streaming responses
docs: add Virtual DB seeding examples
```

Prefixes: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

---

## Testing

Run the test suite before submitting:

```bash
# Verify skill configuration
python3 verify_skill.py

# Run E2E tests (requires authentication)
python3 scripts/test_all_skills.py

# Test streaming
python3 scripts/test_streaming.py

# Test Virtual DB
python3 scripts/test_vdb.py
```

---

## Submitting Changes

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make your changes and test them
3. Commit with a clear message
4. Push to your fork: `git push origin feat/my-feature`
5. Open a Pull Request on [GitHub](https://github.com/thierryteisseire/epsimo-cli/pulls)

### PR guidelines

- Describe what the change does and why
- Reference any related issues
- Keep PRs focused — one feature or fix per PR
- Update documentation if your change affects user-facing behavior

---

## Reporting Issues

Open an issue on [GitHub](https://github.com/thierryteisseire/epsimo-cli/issues) with:

- What you expected to happen
- What actually happened
- Steps to reproduce
- Your environment (OS, Python version, CLI version)

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
