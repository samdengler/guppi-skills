# guppi-skills

Personal collection of CLI tools that double as AI agent skills. Each skill is a standalone Python CLI paired with a [SKILL.md](https://github.com/agent-skills/spec) manifest for agent discovery.

Skills work from the terminal for humans and from agents (Claude Code, Copilot, etc.) via SKILL.md instructions.

## Skills

| Skill | Version | Description |
|-------|---------|-------------|
| [chronicler](chronicler/) | 0.1.0 | Search Chrome browser history and terminal history to research past activity |
| [clipper](clipper/) | 0.1.0 | Copy content to the system clipboard without whitespace noise |
| [courier](courier/) | 0.1.0 | Telegram-based messaging between Claude Desktop and Claude Code |
| [locker](locker/) | 0.1.0 | Encrypted secret storage using OS keychain |
| [paper](paper/) | 0.1.0 | Analyze academic papers using the Feynman Technique |
| [snapper](snapper/) | 0.1.0 | CDP browser screenshots for capturing authenticated web pages |
| [spiker](spiker/) | 0.1.0 | Manage experimental spike projects in a centralized, searchable location |

## Installation

Install any skill with [guppi-cli](https://github.com/samdengler/guppi-cli):

```bash
guppi skill install <name> --source guppi-skills
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
guppi-paper analyze paper.pdf
guppi-snapper capture https://example.com
guppi-spiker new redis-caching
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
