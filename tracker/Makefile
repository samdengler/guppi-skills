# Tracker: a Beads store that Claude Code and Claude Cowork can both use.
#
# Usage on a fresh machine:
#   make init            create the store at $(STORE), install the VM binary and shim
#   make test            round-trip test against a throwaway store
#   make install-skill   symlink SKILL.md into ~/.claude/skills/tracker
#
# The bd version here must match the one mise installs on the Mac
# (~/.dotfiles/mise/config.toml: "github:gastownhall/beads").

BD_VERSION ?= 1.2.2
STORE      ?= $(HOME)/src/github.com/samdengler/tracker
PREFIX     ?= trk
VM_OS      ?= linux
VM_ARCH    ?= arm64

RELEASE_BASE := https://github.com/steveyegge/beads/releases/download/v$(BD_VERSION)
VM_TARBALL   := beads_$(BD_VERSION)_$(VM_OS)_$(VM_ARCH).tar.gz
VM_BINARY    := $(STORE)/bin/bd-$(VM_OS)-$(VM_ARCH)
SKILL_DIR    := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

.PHONY: init vm-binary shim store test install-skill export clean-test

init: store vm-binary shim
	@echo "Store ready at $(STORE)"
	@echo "Next: connect $(STORE) as a folder in Claude Cowork."

store:
	@command -v bd >/dev/null || { echo "bd not on PATH; run ~/.dotfiles/bootstrap.sh"; exit 1; }
	@bd version | grep -q "$(BD_VERSION)" || { echo "bd on PATH is not $(BD_VERSION)"; bd version; exit 1; }
	@mkdir -p $(STORE)/bin
	@[ -d $(STORE)/.git ] || git -C $(STORE) init -q
	@[ -d $(STORE)/.beads ] || (cd $(STORE) && bd init -p $(PREFIX) -q --non-interactive)
	@cp $(SKILL_DIR)templates/AGENTS.md $(STORE)/AGENTS.md
	@cp $(SKILL_DIR)templates/gitignore $(STORE)/.gitignore
	@[ -e $(STORE)/CLAUDE.md ] || ln -s AGENTS.md $(STORE)/CLAUDE.md

vm-binary: $(VM_BINARY)

$(VM_BINARY):
	@mkdir -p $(STORE)/bin
	@tmp=$$(mktemp -d); \
	  curl -fsSL -o $$tmp/$(VM_TARBALL) $(RELEASE_BASE)/$(VM_TARBALL); \
	  curl -fsSL -o $$tmp/checksums.txt $(RELEASE_BASE)/checksums.txt; \
	  (cd $$tmp && grep " $(VM_TARBALL)$$" checksums.txt | shasum -a 256 -c -) || { echo "checksum mismatch"; exit 1; }; \
	  tar xzf $$tmp/$(VM_TARBALL) -C $$tmp bd; \
	  mv $$tmp/bd $@; chmod +x $@; rm -rf $$tmp
	@echo "Installed $@"

shim:
	@cp $(SKILL_DIR)bin/bd $(STORE)/bin/bd && chmod +x $(STORE)/bin/bd

export:
	@$(STORE)/bin/bd export -o issues.jsonl && echo "wrote $(STORE)/issues.jsonl"

test:
	@STORE=$$(mktemp -d)/store $(MAKE) --no-print-directory init >/dev/null && \
	  $(SKILL_DIR)bin/roundtrip.sh $$STORE

install-skill:
	@mkdir -p $(HOME)/.claude/skills
	@ln -sfn $(SKILL_DIR:/=) $(HOME)/.claude/skills/tracker
	@echo "Linked $(HOME)/.claude/skills/tracker -> $(SKILL_DIR:/=)"
