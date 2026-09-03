# guppi-skills

Personal collection of CLI tools that double as AI agent skills. Each skill is a standalone Python CLI paired with a [SKILL.md](https://github.com/agent-skills/spec) manifest for agent discovery.

Skills work from the terminal for humans and from agents (Claude Code, Copilot, etc.) via SKILL.md instructions.

## Design Philosophy

Every skill is a real CLI first. There are no agent-only APIs or hidden interfaces — if an agent can do it, you can do it from your terminal. The SKILL.md manifest just teaches agents which commands exist and when to use them.

This means skills are testable, composable, and useful even without an AI agent. The agent is a caller, not a requirement.

## Skills

| Skill | Version | Status | Description |
|-------|---------|--------|-------------|
| [chronicler](chronicler/) | 0.1.0 | Active | Research historical events from local history sources |
| [clipper](clipper/) | 0.1.0 | Active | Copy content to the system clipboard without whitespace noise |
| [dotfiles](dotfiles/) | 0.1.0 | Active | Add, remove, and reconcile machine dependencies through the dotfiles manifests |
| [courier](courier/) | 0.1.0 | Active | Telegram-based messaging for Claude workflows |
| [futzer](futzer/) | 0.1.0 | Experimental | Opinionated config generator you own and understand |
| [locker](locker/) | 0.1.0 | Active | Deterministic secret storage for guppi skills |
| [paper](paper/) | 0.1.0 | Experimental | Analyze academic papers using the Feynman Technique |
| [shooter](shooter/) | 0.1.0 | Experimental | Screenshot manager — set preferences and manage screen captures |
| [snapper](snapper/) | 0.1.0 | Active | CDP browser screenshots for capturing authenticated web pages |
| [spiker](spiker/) | 0.3.0 | Active | Manage experimental spike projects in a centralized, searchable location |
| [surfer](surfer/) | 0.1.0 | Experimental | Chrome browser automation via AppleScript JavaScript execution |
| [tracker](tracker/) | 0.2.0 | Active | Cross-project task and idea tracker built on beads |

## Installation

Install any skill with [guppi-cli](https://github.com/samdengler/guppi-cli):

```bash
guppi skills install <name> --source guppi-skills
```

Or install directly with [uv](https://docs.astral.sh/uv/):

```bash
cd <skill-name>/
uv tool install .
```

After installing, each skill is available as `guppi-<name>`:

```bash
guppi-chronicler search "github" --since yesterday
guppi-clipper copy myfile.txt
guppi-courier receive
guppi-locker get courier bot-token
guppi-paper prompt https://arxiv.org/abs/2301.00001
guppi-snapper capture https://example.com
guppi-spiker new redis-caching
guppi-tracker add "Try out DuckDB for analytics"
```

Every skill also has a `skill` subcommand for agent integration:

```bash
guppi-<name> skill show      # Display SKILL.md manifest
guppi-<name> skill install   # Register with guppi-cli
```

## Development

### Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for package management

### Working on a skill

```bash
cd <skill-name>/
uv sync                       # Install dependencies
uv run guppi-<name> --help    # Run locally
uv run pytest                  # Run tests
```

### Skill documentation

Each skill has three docs, each for a different audience:

| File | For | Purpose |
|------|-----|---------|
| `README.md` | Users | What it does, how to use it, examples |
| `SKILL.md` | Agents | Instructions Claude follows when invoked |
| `docs/design/` | Developers | Architecture and feature planning |

Browse any skill's directory on GitHub to see its README rendered automatically.

### Creating a new skill

See [CLAUDE.md](CLAUDE.md) for conventions, directory structure, and templates. Skills follow the [Agent Skills](https://github.com/agent-skills/spec) open standard.

### Releasing

Each skill is versioned and tagged independently. See [RELEASE.md](RELEASE.md) for details.

```bash
git tag -a <name>/vX.Y.Z -m "<name> version X.Y.Z"
git push origin <name>/vX.Y.Z
```

## Disclaimer

This is a personal automation toolkit. Use at your own risk. No warranties, no support guarantees.

## License

[MIT](LICENSE)
