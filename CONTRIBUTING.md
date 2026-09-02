# Contributing to CLIWS

Thank you for contributing.

## Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout main
   git pull
   git checkout -b feature/your-change
   ```
2. Make your changes with clear commits.
3. Open a pull request against `main` describing:
   - What problem the change solves
   - How you tested it
   - Any deployment or SQL migration steps
4. Ensure install scripts and documentation remain accurate if you change deployment behavior.

## Guidelines

- Keep storage file-based under the application directory.
- Do not add authentication unless explicitly requested.
- For schema changes, add a new numbered SQL file in `sql/` and bump `CLIWS_SCHEMA_VERSION`.
- Match the existing logging format (EST timestamp, function, line number, rotating file handler).
- Avoid hardcoded paths; use environment variables and install script variables.

## SQL migrations

CLIWS does not auto-migrate. Add scripts like `sql/003_your_change.sql` and document manual application in your PR.

## Pull request checklist

- [ ] README updated if behavior or deployment changed
- [ ] CHANGELOG updated for user-visible features
- [ ] SQL migration added if schema changed
- [ ] Tested on Linux target (or documented limitation)
