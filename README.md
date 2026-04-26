# epsimo-cli

CLI for the [EpsimoAI](https://epsimoai.com) platform — manage AI agents, projects, threads, Virtual Database, and deployments from the terminal.

## Install

```bash
npm install -g epsimo-cli
pip install requests pyyaml click python-dotenv
```

Requires Node.js 16+ and Python 3.8+.

## Quick Start

```bash
epsimo auth                    # Login
epsimo create "My AI App"      # Scaffold a project
cd my-ai-app
epsimo init                    # Link to platform
epsimo deploy                  # Deploy assistants
epsimo run --project-id <ID> --assistant-id <ID>  # Chat
```

## Commands

| Command | Description |
|---------|-------------|
| `epsimo auth` | Authenticate with email/password |
| `epsimo whoami` | Show current user |
| `epsimo projects` | List projects |
| `epsimo init` | Initialize project in current directory |
| `epsimo deploy` | Deploy epsimo.yaml config |
| `epsimo create <name>` | Scaffold new MVP project |
| `epsimo assistants --project-id <ID>` | List assistants |
| `epsimo threads --project-id <ID>` | List threads |
| `epsimo run --project-id <ID> --assistant-id <ID>` | Interactive chat |
| `epsimo db query --project-id <ID> --thread-id <ID>` | Query Virtual Database |
| `epsimo db set --project-id <ID> --thread-id <ID> --key <K> --value <V>` | Set state value |
| `epsimo credits balance` | Check thread balance |
| `epsimo credits buy --quantity <N>` | Purchase threads |

## How It Works

The npm package includes a Node.js wrapper (`bin/epsimo.js`) that invokes `python3 -m epsimo` with the correct `PYTHONPATH`. This bridges npm's global install to the bundled Python CLI.

## License

MIT
