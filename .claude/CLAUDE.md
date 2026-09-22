# Rules for tkinter-task-manager-mvp

## Development workflow

- Always go through **a feature branch → Pull Request → squash merge**. **Never push directly to `main`**
- CI (`.github/workflows/test.yml`) also runs on PRs, so check its results before merging
- Run `pytest` locally before opening a PR when possible — e.g. this may not be possible in a sandboxed Claude Code session where `pytest`/`tkcalendar` aren't installed and network access to install them is blocked; if so, say that explicitly in the PR/report instead of silently skipping

## Language

- Write commit messages, PR titles/descriptions, and Issues in English (as of 2026-09-22)
- Write code comments and docstrings in English (as of 2026-09-22; they used to be in Japanese but have all been translated)
- `README_ja.md` and `README_en.md` must always be updated together — never update only one
