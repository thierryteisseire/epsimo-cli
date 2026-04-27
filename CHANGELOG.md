# Changelog

All notable changes to the Epsimo CLI are documented here.

---

## [0.3.3] — 2026-04-27

### Added
- Comprehensive documentation suite: Getting Started guide, TUI guide, Configuration reference, Virtual DB guide
- CONTRIBUTING.md with development setup and PR guidelines
- CHANGELOG.md (this file)
- API reference with accurate endpoints and SDK-to-API mapping table

### Fixed
- Corrected API base URL in documentation (`https://backend.epsimoagents.com`)
- Fixed documentation links and cross-references

---

## [0.3.0] — 2026-04-26

### Added
- **Interactive TUI dashboard** (`epsimo tui`) with 9 screens: Status, Projects, Assistants, Threads, Virtual DB, Tools, Chat, New Assistant wizard, Buy Threads
- **Smart CLI commands**: `epsimo chat`, `epsimo exec`, `epsimo search`, `epsimo tools`
- Animated spinners for async operations (connecting, thinking, searching, writing, tool calls)
- Slash commands in chat mode with auto-completion (`/help`, `/status`, `/db`, `/tools`, etc.)
- Cross-platform installers: `install.sh` (macOS/Linux), `install.ps1` (Windows)
- `epsimo tools health <type>` — health-check individual tools
- `epsimo chat --tools` — enable specific tools for a chat session
- `epsimo exec --file` — execute code files through an assistant
- Real-time tool call visualization in chat and run modes
- Project auto-detection from `epsimo.yaml` in current directory

### Changed
- Upgraded CLI architecture with `cli_smart.py` for advanced commands
- Improved streaming response handling with deduplication

---

## [0.2.2] — 2026-04-26

### Added
- Working npm bin wrapper (`bin/epsimo.js`)
- npm package configuration for global installation (`npm install -g epsimo-cli`)

### Fixed
- npm binary entry point resolution

---

## [0.2.0] — Initial Release

### Added
- Core CLI commands: `auth`, `whoami`, `projects`, `assistants`, `threads`, `init`, `deploy`, `create`, `run`
- Python SDK (`EpsimoClient`) with resource clients for Projects, Assistants, Threads, Files, Credits, Database
- Virtual Database pattern — thread-based persistent storage
- `epsimo.yaml` configuration file for declarative assistant management
- `epsimo create` — scaffold Next.js projects with Epsimo UI Kit
- `epsimo deploy` — sync assistant configuration to the platform
- `epsimo db query/set` — CLI access to Virtual Database
- `epsimo credits balance/buy` — thread balance and Stripe checkout
- React UI Kit: `ThreadChat` component and `useChat` hook
- Tool library (`epsimo/tools/library.yaml`) with database_sync, web_search_tavily, web_search_ddg, retrieval_optimized, task_management
- JWT token management with auto-refresh
- Project scaffolding templates
- MIT License
