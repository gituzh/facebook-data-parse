# Repository Guidelines

## Project Structure & Module Organization
- `scripts/`: Python tooling and mapping DSL files.
  - `scripts/posts.py`: main parser.
  - `scripts/posts.mapping.json`: mapping rules.
  - `scripts/posts.mapping.md`: mapping reference.
- `data/input/`: place raw Facebook export data here (not committed).
- `data/output/`: generated cleaned JSON output.
- `README.md`: usage and CLI options.

## Build, Test, and Development Commands
- `python3 scripts/posts.py data/input/<facebook-export>/posts/profile_posts_1.json`: run the parser with defaults.
- `python3 scripts/posts.py --mapping scripts/posts.mapping.json --output-dir data/output --sort-field timestamp --sort-order asc --collapse-single-branches --flatten-dicts <input>`: run with explicit options.
- No build step; standard Python 3.9+ is sufficient.

## Coding Style & Naming Conventions
- Python: 4-space indentation; keep functions small and focused.
- File naming: `snake_case.py` for scripts; mapping files use `posts.mapping.*`.
- Prefer clear, explicit variable names over abbreviations.
- No formatter or linter is configured; keep style consistent with `scripts/posts.py`.

## Testing Guidelines
- No automated tests are present.
- If adding tests, place them under a `tests/` directory and name files `test_*.py`.
- Manual verification: run the parser against a sample export and validate `data/output/` JSON.

## Commit & Pull Request Guidelines
- Commit messages follow Conventional Commits (e.g., `feat: ...`, `docs: ...`).
- PRs should include: summary of changes, any new CLI flags, and sample input/output behavior notes.
- If output format changes, update `README.md` and mapping docs.

## Security & Data Handling
- Facebook exports contain sensitive data; avoid committing any files under `data/input/` or `data/output/`.
- Sanitize examples in documentation if they include real user content.
