# Contributing to Pyker

Thanks for helping improve Pyker. This guide keeps contributions small and reviewable.

## Development setup

```bash
git clone https://github.com/mrvi0/pyker.git
cd pyker
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install -e ".[dev]"
```

## Running tests

```bash
pytest -q
```

CI runs the same suite on Python 3.8–3.12.

## Project layout

| Path | Role |
|------|------|
| `pyker/cli.py` | CLI / argparse |
| `pyker/manager.py` | process lifecycle |
| `pyker/store.py` | `~/.pyker` state & config |
| `pyker/hooks.py` | boot/login OS hooks |
| `pyker/watcher.py` | auto-restart watcher |
| `tests/` | smoke tests |

## Pull requests

1. Fork and create a branch from `main`.
2. Keep changes focused (one concern per PR when possible).
3. Add or update tests for behavior changes.
4. Use [Conventional Commits](https://www.conventionalcommits.org/) briefly, e.g.:
   - `feat: ...`
   - `fix: ...`
   - `docs: ...`
   - `test: ...`
   - `chore: ...`
5. Reference issues in the subject when relevant: `fix: handle missing pid (#12)`.
6. Open a PR and fill in the template.

## Reporting bugs / ideas

Use the GitHub issue forms:

- Bug report
- Feature request

Security issues: see [SECURITY.md](SECURITY.md) — do **not** open a public issue.

## Code of conduct

Participation is covered by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
